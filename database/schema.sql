CREATE DATABASE paisapilot;
USE paisapilot;

CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(150) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE accounts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  name VARCHAR(100) NOT NULL,
  type ENUM('cash','bank','upi') NOT NULL,
  balance DECIMAL(12,2) DEFAULT 0,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE categories (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(60) NOT NULL UNIQUE
);

CREATE TABLE transactions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  account_id INT NOT NULL,
  category_id INT,
  amount DECIMAL(12,2) NOT NULL,
  type ENUM('income','expense') NOT NULL,
  description VARCHAR(255),
  txn_date DATE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (account_id) REFERENCES accounts(id),
  FOREIGN KEY (category_id) REFERENCES categories(id),
  INDEX idx_user_date (user_id, txn_date)
);

INSERT INTO categories (name) VALUES
('Food'),('Travel'),('Bills'),('Shopping'),('Health'),('Salary'),('Other');



USE paisapilot;

ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0;
UPDATE users SET is_admin = 1 WHERE email = 'YOUR_EMAIL_HERE';

CREATE TABLE savings_goals (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  title VARCHAR(100) NOT NULL,
  target_amount DECIMAL(12,2) NOT NULL,
  saved_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
  target_date DATE NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE recurring_bills (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  category_id INT NULL,
  title VARCHAR(100) NOT NULL,
  amount DECIMAL(12,2) NOT NULL,
  due_day TINYINT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT 1,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE audit_log (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NULL,
  action VARCHAR(50) NOT NULL,
  table_name VARCHAR(50) NOT NULL,
  record_id INT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_audit_created (created_at)
);

DROP TRIGGER IF EXISTS trg_audit_txn_update;
DROP TRIGGER IF EXISTS trg_audit_txn_delete;
DELIMITER //
CREATE TRIGGER trg_audit_txn_update AFTER UPDATE ON transactions
FOR EACH ROW
BEGIN
  INSERT INTO audit_log (user_id, action, table_name, record_id)
  VALUES (NEW.user_id, 'UPDATE', 'transactions', NEW.id);
END//
CREATE TRIGGER trg_audit_txn_delete AFTER DELETE ON transactions
FOR EACH ROW
BEGIN
  INSERT INTO audit_log (user_id, action, table_name, record_id)
  VALUES (OLD.user_id, 'DELETE', 'transactions', OLD.id);
END//
DELIMITER ;