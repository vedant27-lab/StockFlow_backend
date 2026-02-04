/*
CREATE TABLE product_fields (
    id INT AUTO_INCREMENT PRIMARY KEY,
    field_name VARCHAR(100) NOT NULL,
    field_type ENUM('text','number','date','boolean','dropdown') NOT NULL,
    is_required BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE
);
CREATE TABLE product_field_values (
	id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    field_id INT NOT NULL,
    value TEXT,
    
    FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE CASCADE,
    FOREIGN KEY (field_id) REFERENCES product_fields(id) ON DELETE CASCADE,
    
    UNIQUE (product_id, field_id)
);


USE stockflow;

INSERT INTO product_fields (field_name, field_type, is_required)
VALUES
('price', 'number', 1),
('color', 'text', 0),
('quantity', 'number', 1PRIMARY);


CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(150) UNIQUE,
    role ENUM('admin','user') DEFAULT 'user'
);

CREATE TABLE permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE
);


INSERT INTO permissions (name) VALUES
('CREATE_PRODUCT'),
('UPDATE_PRODUCT'),
('DELETE_PRODUCT'),
('MANAGE_FIELDS');


CREATE TABLE user_permissions (
	user_id INT,
    permission_id INT,
    PRIMARY KEY (user_id, permission_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);
*/

-- INSERT INTO users (name, email, role)
-- VALUES ('Admin User', 'admin@stockflow.com', 'admin');

/*
USE stockflow;
SELECT 
    u.name,
    p.name AS permission
FROM user_permissions up
JOIN users u ON up.user_id = u.id
JOIN permissions p ON up.permission_id = p.id;



CREATE TABLE product_folders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE product_fields
ADD COLUMN folder_id INT,
ADD CONSTRAINT fk_field_folder	FOREIGN KEY (folder_id) REFERENCES product_folders(id) ON DELETE CASCADE;

ALTER TABLE products
ADD COLUMN folder_id INT,
ADD CONSTRAINT fk_field_folder FOREIGN KEY (folder_id) REFERENCES product_folders(id) ON DELETE CASCADE;

USE stockflow;
CREATE TABLE IF NOT EXISTS product_folders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE products ADD COLUMN folder_id INT;
ALTER TABLE product_fields ADD COLUMN folder_id INT;

ALTER TABLE product_fields 
ADD COLUMN is_analytics_target BOOLEAN DEFAULT 0;


ALTER TABLE products DROP COLUMN quantity;
*/

ALTER TABLE product_fields 
ADD COLUMN is_analytics_target BOOLEAN DEFAULT 0;



