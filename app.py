# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import sys

# Initialize the Flask application
app = Flask(__name__)

# --- Configuration ---
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_super_secret_key_here')
# MariaDB connection (XAMPP, default root with no password)
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'flask_db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the SQLAlchemy object
db = SQLAlchemy(app)

# --- Database Models ---
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    position = db.Column(db.String(100))
    hire_date = db.Column(db.Date)
    base_salary = db.Column(db.Numeric(10, 2), nullable=False)

    payrolls = db.relationship('Payroll', back_populates='employee')

class Payroll(db.Model):
    __tablename__ = 'payroll'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    pay_date = db.Column(db.Date, nullable=False)
    hours_worked = db.Column(db.Numeric(10, 2), nullable=False)
    base_salary_at_pay = db.Column(db.Numeric(10, 2), nullable=False)
    bonus = db.Column(db.Numeric(10, 2), default=0.00)
    deductions = db.Column(db.Numeric(10, 2), default=0.00)
    gross_pay = db.Column(db.Numeric(10, 2), nullable=False)
    net_pay = db.Column(db.Numeric(10, 2), nullable=False)

    employee = db.relationship('Employee', back_populates='payrolls')
# Create the database tables
with app.app_context():
    db.create_all()

# --- Decorator for login required routes ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---
@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('index.html', title='Home')
    flash('Please log in to continue.', 'info')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check your username and password.', 'danger')
    return render_template('login.html', title='Login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'warning')
            return redirect(url_for('register'))
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# --- Employee Management ---
@app.route('/employees')
@login_required
def view_employees():
    employees = Employee.query.all()
    return render_template('view_employees.html', employees=employees)

@app.route('/employees/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    if request.method == 'POST':
        try:
            new_employee = Employee(
                first_name=request.form['first_name'],
                last_name=request.form['last_name'],
                email=request.form['email'],
                position=request.form['position'],
                hire_date=request.form['hire_date'],
                base_salary=float(request.form['base_salary'])
            )
            db.session.add(new_employee)
            db.session.commit()
            flash('Employee added successfully!', 'success')
            return redirect(url_for('view_employees'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding employee: {e}", 'danger')
    return render_template('add_employee.html')

@app.route('/employees/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    employee = Employee.query.get_or_404(id)
    if request.method == 'POST':
        try:
            employee.first_name = request.form['first_name']
            employee.last_name = request.form['last_name']
            employee.email = request.form['email']
            employee.position = request.form['position']
            employee.hire_date = request.form['hire_date']
            employee.base_salary = float(request.form['base_salary'])
            db.session.commit()
            flash('Employee updated successfully!', 'success')
            return redirect(url_for('view_employees'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating employee: {e}", 'danger')
    return render_template('edit_employee.html', employee=employee)

@app.route('/employees/delete/<int:id>', methods=['POST'])
@login_required
def delete_employee(id):
    employee = Employee.query.get_or_404(id)
    try:
        db.session.delete(employee)
        db.session.commit()
        flash('Employee deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting employee: {e}", 'danger')
    return redirect(url_for('view_employees'))

# --- Payroll Management ---
@app.route('/payroll/generate', methods=['GET', 'POST'])
@login_required
def generate_payroll():
    employees = Employee.query.all()
    if request.method == 'POST':
        try:
            employee_id = request.form['employee_id']
            pay_date = request.form['pay_date']
            hours_worked = float(request.form['hours_worked'])
            bonus = float(request.form.get('bonus', 0))
            deductions = float(request.form.get('deductions', 0))

            employee = Employee.query.get(employee_id)
            if not employee:
                flash("Employee not found.", 'danger')
                return redirect(url_for('generate_payroll'))
            
            hourly_rate = employee.base_salary / 160
            gross_pay = (hourly_rate * hours_worked) + bonus
            net_pay = gross_pay - deductions

            new_payroll = Payroll(
                employee_id=employee_id,
                pay_date=pay_date,
                hours_worked=hours_worked,
                base_salary_at_pay=employee.base_salary,
                bonus=bonus,
                deductions=deductions,
                gross_pay=gross_pay,
                net_pay=net_pay
            )
            db.session.add(new_payroll)
            db.session.commit()
            flash('Payroll generated successfully!', 'success')
            return redirect(url_for('view_payrolls'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error generating payroll: {e}", 'danger')
    return render_template('generate_payroll.html', employees=employees)

@app.route('/payrolls')
@login_required
def view_payrolls():
    payrolls = Payroll.query.order_by(Payroll.pay_date.desc()).all()
    return render_template('view_payrolls.html', payrolls=payrolls)

if __name__ == '__main__':
    app.run(debug=True)