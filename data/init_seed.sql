-- Initial Seed Script for Text-to-SQL Enterprise Database (~100MB+ data size)
-- Executed automatically upon PostgreSQL container initialization

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INT DEFAULT 100,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'completed',
    shipping_zip VARCHAR(20) DEFAULT '90210',
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id) ON DELETE CASCADE,
    product_id INT REFERENCES products(id) ON DELETE CASCADE,
    quantity INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(10, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    performed_by VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed Hand-Curated Golden Test Data First
INSERT INTO users (id, username, email, status, created_at) VALUES
(1, 'alice_smith', 'alice@example.com', 'active', '2024-01-15 10:00:00'),
(2, 'john_doe', 'john@example.com', 'active', '2024-02-01 11:30:00'),
(3, 'charlie_brown', 'charlie@example.com', 'inactive', '2023-11-20 09:15:00'),
(4, 'david_miller', 'david@example.com', 'active', '2024-03-10 14:20:00')
ON CONFLICT (username) DO NOTHING;

-- Bulk Seed Additional Users (25,000 Users)
INSERT INTO users (username, email, status, created_at)
SELECT 
    'user_' || g AS username,
    'user_' || g || '@enterprise-domain.com' AS email,
    (ARRAY['active', 'active', 'active', 'inactive', 'pending', 'suspended'])[floor(random() * 6 + 1)] AS status,
    TIMESTAMP '2023-01-01 00:00:00' + (random() * (NOW() - TIMESTAMP '2023-01-01 00:00:00')) AS created_at
FROM generate_series(5, 25000) AS g
ON CONFLICT (username) DO NOTHING;

-- Seed Hand-Curated Golden Products
INSERT INTO products (id, name, category, price, stock_quantity, created_at) VALUES
(1, 'Laptop Pro 15', 'Electronics', 1299.99, 45, '2024-01-01 00:00:00'),
(2, 'Wireless Mouse', 'Electronics', 29.99, 150, '2024-01-01 00:00:00'),
(3, 'Mechanical Keyboard', 'Electronics', 89.99, 80, '2024-01-01 00:00:00'),
(4, 'SQL Engineering Guide', 'Books', 49.99, 200, '2024-01-05 00:00:00'),
(5, 'Ergonomic Office Chair', 'Furniture', 249.99, 30, '2024-01-10 00:00:00'),
(6, 'Coffee Mug 16oz', 'Kitchenware', 14.99, 0, '2024-01-12 00:00:00')
ON CONFLICT (id) DO NOTHING;

-- Bulk Seed Additional Products (8,000 Products)
INSERT INTO products (name, category, price, stock_quantity, created_at)
SELECT 
    (ARRAY['Ultra', 'Pro', 'Smart', 'Eco', 'Deluxe', 'Compact', 'Precision', 'Enterprise'])[floor(random() * 8 + 1)] || ' ' ||
    (ARRAY['Gadget', 'Device', 'Widget', 'Module', 'Tool', 'Appliance', 'Kit', 'Item'])[floor(random() * 8 + 1)] || ' ' || g AS name,
    (ARRAY['Electronics', 'Books', 'Furniture', 'Kitchenware', 'Clothing', 'Software', 'Sports', 'Automotive'])[floor(random() * 8 + 1)] AS category,
    ROUND((random() * 495 + 5)::numeric, 2) AS price,
    floor(random() * 500)::int AS stock_quantity,
    TIMESTAMP '2023-01-01 00:00:00' + (random() * (NOW() - TIMESTAMP '2023-01-01 00:00:00')) AS created_at
FROM generate_series(7, 8000) AS g;

-- Bulk Seed Orders (300,000 Orders)
INSERT INTO orders (user_id, amount, status, shipping_zip, order_date)
SELECT 
    floor(random() * 24996 + 1)::int AS user_id,
    ROUND((random() * 980 + 10)::numeric, 2) AS amount,
    (ARRAY['completed', 'completed', 'completed', 'pending', 'shipped', 'cancelled', 'refunded'])[floor(random() * 7 + 1)] AS status,
    LPAD(floor(random() * 89999 + 10000)::text, 5, '0') AS shipping_zip,
    TIMESTAMP '2023-01-01 00:00:00' + (random() * (NOW() - TIMESTAMP '2023-01-01 00:00:00')) AS order_date
FROM generate_series(1, 300000) AS g;

-- Bulk Seed Order Items (550,000 Order Items)
INSERT INTO order_items (order_id, product_id, quantity, unit_price)
SELECT 
    floor(random() * 299990 + 1)::int AS order_id,
    floor(random() * 7990 + 1)::int AS product_id,
    floor(random() * 5 + 1)::int AS quantity,
    ROUND((random() * 190 + 10)::numeric, 2) AS unit_price
FROM generate_series(1, 550000) AS g;

-- Bulk Seed Audit Logs (300,000 Audit Logs)
INSERT INTO audit_logs (action, performed_by, timestamp)
SELECT 
    (ARRAY['USER_LOGIN', 'ORDER_CREATED', 'PAYMENT_PROCESSED', 'PRODUCT_UPDATED', 'STOCK_ADJUSTMENT', 'SCHEMA_CHECKED', 'SECURITY_AUDIT'])[floor(random() * 7 + 1)] AS action,
    'user_' || floor(random() * 24996 + 1)::text AS performed_by,
    TIMESTAMP '2023-01-01 00:00:00' + (random() * (NOW() - TIMESTAMP '2023-01-01 00:00:00')) AS timestamp
FROM generate_series(1, 300000) AS g;
