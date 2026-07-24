-- Initial Seed Script for Text-to-SQL Enterprise Database
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

-- Seed Users
INSERT INTO users (username, email, status, created_at) VALUES
('alice_smith', 'alice@example.com', 'active', '2024-01-15 10:00:00'),
('john_doe', 'john@example.com', 'active', '2024-02-01 11:30:00'),
('charlie_brown', 'charlie@example.com', 'inactive', '2023-11-20 09:15:00'),
('david_miller', 'david@example.com', 'active', '2024-03-10 14:20:00')
ON CONFLICT (username) DO NOTHING;

-- Seed Products
INSERT INTO products (name, category, price, stock_quantity) VALUES
('Laptop Pro 15', 'Electronics', 1299.99, 45),
('Wireless Mouse', 'Electronics', 29.99, 150),
('Mechanical Keyboard', 'Electronics', 89.99, 80),
('SQL Engineering Guide', 'Books', 49.99, 200),
('Ergonomic Office Chair', 'Furniture', 249.99, 30),
('Coffee Mug 16oz', 'Kitchenware', 14.99, 0)
ON CONFLICT DO NOTHING;

-- Seed Orders
INSERT INTO orders (id, user_id, amount, status, shipping_zip, order_date) VALUES
(1001, 1, 1329.98, 'completed', '90210', '2024-03-01 12:00:00'),
(1002, 2, 89.99, 'completed', '10001', '2024-03-05 15:45:00'),
(1003, 1, 49.99, 'completed', '90210', '2024-03-12 09:30:00'),
(1004, 4, 249.99, 'pending', '94105', '2024-03-15 16:10:00'),
(1005, 2, 14.99, 'refunded', '10001', '2024-02-18 10:05:00')
ON CONFLICT (id) DO NOTHING;

-- Seed Order Items
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(1001, 1, 1, 1299.99),
(1001, 2, 1, 29.99),
(1002, 3, 1, 89.99),
(1003, 4, 1, 49.99),
(1004, 5, 1, 249.99),
(1005, 6, 1, 14.99)
ON CONFLICT DO NOTHING;
