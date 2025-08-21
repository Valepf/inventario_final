-- test_seeder.sql (PLAIN TEXT passwords)
USE mi_inventario;

SET FOREIGN_KEY_CHECKS = 0;

-- Usuarios con contraseñas en TEXTO PLANO (sin hash)
-- Admin: admin / adminpassword
-- Users: user1 / user123, user2 / user123
DELETE FROM users;
INSERT INTO users (username, password, role) VALUES
('admin', 'adminpassword', 'admin'),
('user1', 'user123', 'general'),
('user2', 'user123', 'general');

-- Categorías
DELETE FROM categories;
INSERT INTO categories (name) VALUES
('Electrónica'),
('Hogar'),
('Jardinería'),
('Deportes');

-- Productos (sin supplier_id: queda NULL por defecto)
DELETE FROM products;
INSERT INTO products (name, description, price, stock, category_id, user_id) VALUES
('Laptop', 'Portátil de alta gama', 800.00, 10, 1, 1),
('Silla', 'Silla ergonómica para oficina', 50.00, 25, 2, 2),
('Cortadora de césped', 'Herramienta para mantener el jardín', 150.00, 5, 3, 1),
('Pelota de fútbol', 'Balón profesional', 20.00, 50, 4, 2);

-- Proveedores
DELETE FROM suppliers;
INSERT INTO suppliers (name, contact) VALUES
('Proveedor A', 'contactoA@mail.com'),
('Proveedor B', 'contactoB@mail.com');

-- Relación productos-proveedores (M:N)
DELETE FROM product_suppliers;
INSERT INTO product_suppliers (product_id, supplier_id) VALUES
(1, 1),
(2, 2),
(3, 1),
(4, 2);

-- Órdenes de ejemplo
DELETE FROM orders;
INSERT INTO orders (product_id, quantity, status, user_id) VALUES
(1, 2, 'pending', 2),
(2, 1, 'completed', 1),
(3, 4, 'pending', 1),
(4, 10, 'completed', 2);

SET FOREIGN_KEY_CHECKS = 1;
