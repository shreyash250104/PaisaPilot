USE paisapilot;

CREATE OR REPLACE VIEW v_monthly_category_spend AS
SELECT user_id,
       DATE_FORMAT(txn_date, '%Y-%m') AS month_year,
       category_id,
       SUM(amount) AS total_spent
FROM transactions
WHERE type = 'expense'
GROUP BY user_id, DATE_FORMAT(txn_date, '%Y-%m'), category_id;

CREATE OR REPLACE VIEW v_monthly_totals AS
SELECT user_id,
       DATE_FORMAT(txn_date, '%Y-%m') AS month_year,
       SUM(CASE WHEN type = 'income'  THEN amount ELSE 0 END) AS income,
       SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) AS expense
FROM transactions
GROUP BY user_id, DATE_FORMAT(txn_date, '%Y-%m');