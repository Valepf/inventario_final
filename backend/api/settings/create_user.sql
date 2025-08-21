-- create_user.sql 

-- Crear usuarios si no existen
CREATE USER IF NOT EXISTS 'mi_inventario'@'localhost' IDENTIFIED BY 'inventariopassword';
CREATE USER IF NOT EXISTS 'mi_inventario'@'127.0.0.1' IDENTIFIED BY 'inventariopassword';

-- Conceder privilegios sobre la BD
GRANT ALL PRIVILEGES ON mi_inventario.* TO 'mi_inventario'@'localhost' WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON mi_inventario.* TO 'mi_inventario'@'127.0.0.1' WITH GRANT OPTION;

-- Aplicar cambios
FLUSH PRIVILEGES;

