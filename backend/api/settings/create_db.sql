-- create_db.sql (estructura + vistas)
-- Crea la base y todas las tablas con FKs coherentes (RESTRICT donde corresponde).

-- Creación de la base de datos
CREATE DATABASE IF NOT EXISTS mi_inventario
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Seleccionar la base de datos
USE mi_inventario;

-- Desactivar verificaciones de claves externas mientras se recrea el esquema
SET FOREIGN_KEY_CHECKS = 0;

-- Borrar vistas si existieran (orden seguro)
DROP VIEW IF EXISTS orders_history;
DROP VIEW IF EXISTS orders_by_category;
DROP VIEW IF EXISTS low_stock_products;
DROP VIEW IF EXISTS current_inventory;

-- Borrar tablas existentes (orden seguro)
DROP TABLE IF EXISTS product_suppliers;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS suppliers;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS users;

-- Crear la tabla de usuarios
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'general') NOT NULL DEFAULT 'general',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Crear la tabla de categorías
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Crear la tabla de proveedores (compatibilidad con email/phone opcionales)
CREATE TABLE IF NOT EXISTS suppliers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    contact VARCHAR(255) NOT NULL,
    email VARCHAR(120) NULL,
    phone VARCHAR(50) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Crear la tabla de productos (incluye supplier_id opcional)
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INT NOT NULL DEFAULT 0,
    category_id INT NULL,
    user_id INT NULL,
    supplier_id INT NULL,
    KEY fk_products_category (category_id),
    KEY idx_products_supplier_id (supplier_id),
    KEY user_id (user_id),
    CONSTRAINT fk_products_category FOREIGN KEY (category_id) REFERENCES categories(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_products_user FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_products_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Crear la tabla de órdenes (historial preservado: RESTRICT contra products)
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    order_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    receipt_date DATETIME NULL,
    status ENUM('pending', 'completed') NOT NULL DEFAULT 'pending',
    user_id INT NULL,
    KEY product_id (product_id),
    KEY user_id (user_id),
    CONSTRAINT fk_orders_product FOREIGN KEY (product_id) REFERENCES products(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Crear la relación productos-proveedores (M:N)
CREATE TABLE IF NOT EXISTS product_suppliers (
    product_id INT NOT NULL,
    supplier_id INT NOT NULL,
    PRIMARY KEY (product_id, supplier_id),
    KEY supplier_id (supplier_id),
    CONSTRAINT fk_ps_product  FOREIGN KEY (product_id)  REFERENCES products(id)  ON DELETE CASCADE,
    CONSTRAINT fk_ps_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Reactivar verificaciones de claves externas
SET FOREIGN_KEY_CHECKS = 1;

-- Crear vistas (sin DEFINER / portables)
CREATE OR REPLACE VIEW orders_by_category AS
SELECT 
    c.name AS category_name,
    SUM(o.quantity) AS total_quantity,
    COUNT(o.id) AS total_orders
FROM orders o
JOIN products p ON o.product_id = p.id
JOIN categories c ON p.category_id = c.id
GROUP BY c.name;

CREATE OR REPLACE VIEW low_stock_products AS
SELECT 
    p.name AS product_name,
    p.stock,
    c.name AS category_name
FROM products p
JOIN categories c ON p.category_id = c.id
WHERE p.stock < 10;

CREATE OR REPLACE VIEW current_inventory AS
SELECT 
    p.name AS product_name,
    p.description,
    p.price,
    p.stock,
    c.name AS category_name
FROM products p
JOIN categories c ON p.category_id = c.id;

CREATE OR REPLACE VIEW orders_history AS
SELECT 
    o.id AS order_id,
    p.name AS product_name,
    o.quantity,
    o.order_date,
    o.receipt_date,
    o.status,
    u.username AS ordered_by
FROM orders o
JOIN products p ON o.product_id = p.id
JOIN users u ON o.user_id = u.id;
