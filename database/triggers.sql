USE paisapilot;

CREATE TABLE expense_groups (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  created_by INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE group_members (
  group_id INT NOT NULL,
  user_id INT NOT NULL,
  joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (group_id, user_id),
  FOREIGN KEY (group_id) REFERENCES expense_groups(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE shared_expenses (
  id INT AUTO_INCREMENT PRIMARY KEY,
  group_id INT NOT NULL,
  paid_by INT NOT NULL,
  amount DECIMAL(12,2) NOT NULL,
  description VARCHAR(255),
  split_type ENUM('equal','custom') NOT NULL,
  expense_date DATE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (group_id) REFERENCES expense_groups(id),
  FOREIGN KEY (paid_by) REFERENCES users(id)
);

CREATE TABLE expense_splits (
  id INT AUTO_INCREMENT PRIMARY KEY,
  expense_id INT NOT NULL,
  user_id INT NOT NULL,
  share_amount DECIMAL(12,2) NOT NULL,
  FOREIGN KEY (expense_id) REFERENCES shared_expenses(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_split_expense (expense_id)
);

CREATE TABLE settlements (
  id INT AUTO_INCREMENT PRIMARY KEY,
  group_id INT NOT NULL,
  from_user INT NOT NULL,
  to_user INT NOT NULL,
  amount DECIMAL(12,2) NOT NULL,
  settled_on DATE NOT NULL,
  FOREIGN KEY (group_id) REFERENCES expense_groups(id),
  FOREIGN KEY (from_user) REFERENCES users(id),
  FOREIGN KEY (to_user) REFERENCES users(id),
  INDEX idx_settle_group (group_id)
);


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