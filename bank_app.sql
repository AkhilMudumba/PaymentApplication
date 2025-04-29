-- Create the database
CREATE DATABASE IF NOT EXISTS banking_app;

-- Select the database
USE banking_app;

-- Create the 'users' table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    card_number VARCHAR(255) NOT NULL,
    expiry_date VARCHAR(10) NOT NULL,
    cvc VARCHAR(4) NOT NULL,
    account_number VARCHAR(12) NOT NULL UNIQUE,  -- Ensures account number is unique
    balance DECIMAL(10, 2) DEFAULT 100.00,       -- Default balance set to 100
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create the 'transactions' table
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    amount DECIMAL(10, 2) NOT NULL,
    recipient_name VARCHAR(255) NOT NULL,
    sender_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create the 'app_users' table
CREATE TABLE IF NOT EXISTS app_users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    account_number VARCHAR(12) NOT NULL UNIQUE  -- Ensures account number is unique
);
