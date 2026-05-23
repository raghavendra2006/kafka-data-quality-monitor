-- =============================================
-- Source Database Seed Script
-- Products and Sales tables with sample data
-- =============================================

-- Create products table
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);

-- Create sales table
CREATE TABLE IF NOT EXISTS sales (
    sale_id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(product_id),
    sale_date TIMESTAMP NOT NULL DEFAULT NOW(),
    quantity INT NOT NULL CHECK (quantity > 0),
    total_amount DECIMAL(12, 2) NOT NULL
);

-- Seed products
INSERT INTO products (product_id, name, category, price) VALUES
(1, 'Wireless Bluetooth Headphones', 'Electronics', 79.99),
(2, 'Organic Green Tea (50 bags)', 'Grocery', 12.49),
(3, 'Stainless Steel Water Bottle', 'Kitchen', 24.95),
(4, 'Running Shoes - Men', 'Sports', 119.99),
(5, 'USB-C Hub 7-in-1', 'Electronics', 45.00),
(6, 'Yoga Mat Premium', 'Sports', 34.99),
(7, 'Cast Iron Skillet 12"', 'Kitchen', 39.95),
(8, 'Mechanical Keyboard RGB', 'Electronics', 89.99),
(9, 'Protein Powder Vanilla 2lb', 'Grocery', 29.99),
(10, 'LED Desk Lamp', 'Electronics', 42.50),
(11, 'Trail Running Backpack 15L', 'Sports', 64.99),
(12, 'French Press Coffee Maker', 'Kitchen', 27.99),
(13, 'Wireless Mouse Ergonomic', 'Electronics', 35.00),
(14, 'Almond Butter Organic 16oz', 'Grocery', 9.99),
(15, 'Resistance Bands Set', 'Sports', 19.99),
(16, 'Ceramic Non-Stick Pan Set', 'Kitchen', 89.99),
(17, 'Portable SSD 1TB', 'Electronics', 109.99),
(18, 'Whey Protein Bars (12 pack)', 'Grocery', 24.99),
(19, 'Foam Roller 18"', 'Sports', 22.50),
(20, 'Electric Kettle 1.7L', 'Kitchen', 32.99)
ON CONFLICT (product_id) DO NOTHING;

-- Seed sales
INSERT INTO sales (sale_id, product_id, sale_date, quantity, total_amount) VALUES
(1, 1, '2024-01-15 10:30:00', 2, 159.98),
(2, 3, '2024-01-15 11:45:00', 1, 24.95),
(3, 5, '2024-01-15 14:20:00', 3, 135.00),
(4, 2, '2024-01-16 09:10:00', 5, 62.45),
(5, 8, '2024-01-16 12:00:00', 1, 89.99),
(6, 4, '2024-01-16 15:30:00', 1, 119.99),
(7, 6, '2024-01-17 08:45:00', 2, 69.98),
(8, 10, '2024-01-17 10:15:00', 1, 42.50),
(9, 7, '2024-01-17 13:00:00', 2, 79.90),
(10, 9, '2024-01-18 09:30:00', 3, 89.97),
(11, 1, '2024-01-18 11:00:00', 1, 79.99),
(12, 12, '2024-01-18 14:45:00', 4, 111.96),
(13, 14, '2024-01-19 10:00:00', 6, 59.94),
(14, 11, '2024-01-19 11:30:00', 1, 64.99),
(15, 15, '2024-01-19 16:00:00', 2, 39.98),
(16, 13, '2024-01-20 09:15:00', 1, 35.00),
(17, 16, '2024-01-20 12:30:00', 1, 89.99),
(18, 17, '2024-01-20 14:00:00', 2, 219.98),
(19, 18, '2024-01-21 08:30:00', 3, 74.97),
(20, 19, '2024-01-21 10:45:00', 1, 22.50),
(21, 20, '2024-01-21 13:15:00', 2, 65.98),
(22, 3, '2024-01-22 09:00:00', 3, 74.85),
(23, 5, '2024-01-22 11:30:00', 1, 45.00),
(24, 8, '2024-01-22 14:00:00', 2, 179.98),
(25, 2, '2024-01-23 10:00:00', 4, 49.96)
ON CONFLICT (sale_id) DO NOTHING;

-- Reset sequences
SELECT setval('products_product_id_seq', (SELECT MAX(product_id) FROM products));
SELECT setval('sales_sale_id_seq', (SELECT MAX(sale_id) FROM sales));
