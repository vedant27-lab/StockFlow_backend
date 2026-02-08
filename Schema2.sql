CREATE DATABASE stockflow2;
USE stockflow2;

-- 1. Folders (Categories like Electronics, Groceries)
CREATE TABLE IF NOT EXISTS folders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

-- 2. Products (The Items)
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    folder_id INT,
    FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE CASCADE
);

-- 3. Fields (Definitions like "Price", "Qty", "Weight")
CREATE TABLE IF NOT EXISTS fields (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    field_type ENUM('text', 'number') DEFAULT 'text', -- Crucial for auto-detection
    folder_id INT,
    FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE CASCADE
);

-- 4. Values (The actual data)
CREATE TABLE IF NOT EXISTS field_values (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    field_id INT,
    value TEXT, -- We store everything as text, but cast to number when needed
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE
);