-- database.sql
-- Create the database
CREATE DATABASE IF NOT EXISTS payroll_db;

-- Use the database
USE payroll_db;

-- Create the employees table
CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    position VARCHAR(100),
    hire_date DATE,
    base_salary DECIMAL(10, 2) NOT NULL
);

-- Create the payroll table
CREATE TABLE IF NOT EXISTS payroll (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    pay_date DATE NOT NULL,
    hours_worked DECIMAL(10, 2) NOT NULL,
    base_salary_at_pay DECIMAL(10, 2) NOT NULL, -- Store base salary at time of payroll for historical accuracy
    bonus DECIMAL(10, 2) DEFAULT 0.00,
    deductions DECIMAL(10, 2) DEFAULT 0.00,
    gross_pay DECIMAL(10, 2) NOT NULL,
    net_pay DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);

