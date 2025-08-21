# Sistema de Gestión de Inventario

Aplicación desarrollada con **Flask (Python)**, **MySQL (XAMPP)** y un frontend en **HTML, CSS y JavaScript**.
Permite la gestión de productos, categorías, proveedores, órdenes y reportes de inventario.

## Requisitos
- Python 3.10 o superior
- XAMPP con MySQL activo
- Visual Studio Code (opcional)
- Thunder Client o Postman (opcional, para probar la API)

## Instalación del entorno
1. Clonar el repositorio:
   ```bash
   git clone https://github.com/TU-USUARIO/inventario.git
   cd inventario/backend
   ```
2. Crear y activar entorno virtual:
   - Windows:
     ```bash
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     python -m venv .venv
     source .venv/bin/activate
     ```
3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Inicialización de la base de datos (phpMyAdmin o consola)
> **Orden recomendado:** `create_db.sql` → `create_user.sql` (opcional) → `test_seeder.sql`.

### Opción A: phpMyAdmin
1. Iniciar **MySQL** en XAMPP y abrir **phpMyAdmin**.
2. Menú **Importar** → seleccionar el archivo `db/create_db.sql` → Ejecutar.
3. (Opcional) Importar `db/create_user.sql` si se desea crear el usuario `mi_inventario` distinto de `root`.
4. Importar `db/test_seeder.sql` para cargar datos de prueba.

### Opción B: consola
```bash
# Usando el cliente mysql (ajustar ruta/usuario/clave si es necesario)
mysql -u root -p < db/create_db.sql
mysql -u root -p < db/test_seeder.sql
# (Opcional) crear usuario dedicado
mysql -u root -p < db/create_user.sql
```

## Ejecución de la aplicación
Desde la carpeta `backend/`:
```bash
set FLASK_APP=main.py   # Windows CMD
set FLASK_ENV=development
flask run
# Navegar a http://localhost:5000
```
En Linux/Mac:
```bash
export FLASK_APP=main.py
export FLASK_ENV=development
flask run
```

## Políticas de consistencia y borrado
- **Products → Categories:** `ON DELETE RESTRICT`. No es posible eliminar una categoría si existen productos asociados. La eliminación debe realizarse **reasignando** los productos a otra categoría desde la interfaz/endpoint correspondiente.
- **Orders → Products:** `ON DELETE RESTRICT`. El historial de órdenes se preserva incluso si se desea eliminar un producto; primero debe resolverse el vínculo (cancelar/archivar).
- **Products → Suppliers (opcional):** `ON DELETE SET NULL` si se usa `supplier_id` directo. Además existe la tabla `product_suppliers` para relaciones M:N.
- Las **vistas** (`current_inventory`, `low_stock_products`, `orders_by_category`, `orders_history`) se crean **sin `DEFINER`**, para evitar problemas de permisos al importar en equipos distintos.

## Datos de prueba
- Los usuarios y datos iniciales se cargan con `db/test_seeder.sql`.
- Las contraseñas están **hasheadas con scrypt**. Si necesitás contraseñas específicas, reemplaza los hashes en el seeder por los que produzca tu backend o solicita un seeder alternativo.


## Ingreso según rol

**Administración (rol: `admin`)**
- Usuario: `admin`
- Permisos: acceso total (productos, categorías, proveedores, reportes). La eliminación de categorías requiere **reasignar** productos previamente (política ON DELETE RESTRICT).

**Usuario general (rol: `general`)**
- Usuarios de ejemplo: `user1`, `user2`
- Permisos: creación/lectura de órdenes y productos según las reglas de negocio. No puede eliminar categorías con productos ni acceder a funciones administrativas.

**Contraseñas**
- Las contraseñas se cargan desde `db/test_seeder.sql` y están **hasheadas con scrypt**.
- Si preferís usar contraseñas conocidas (ej. `admin123` / `user123`), reemplazá los valores de `password` en el seeder por hashes scrypt válidos.
  - Hashes scrypt de ejemplo: ver `demo_hashes.txt` incluido en la entrega (generados con `werkzeug.security.generate_password_hash`).

## Ingreso según rol

**Administración (rol: `admin`)**
- Usuario: `admin`
- Contraseña: `adminpassword`
- Permisos: acceso total (productos, categorías, proveedores, reportes). La eliminación de categorías requiere **reasignar** productos previamente (ON DELETE RESTRICT).

**Usuario general (rol: `general`)**
- Usuarios: `user1` y `user2`
- Contraseña: `user123`
- Permisos: creación/lectura de órdenes y productos según las reglas de negocio. Sin acceso a funciones administrativas.

**Notas sobre contraseñas**
- Las contraseñas del entorno de prueba están en **texto plano** en `db/test_seeder.sql` (sin hash).
- Si el backend tenía validación con hash (p. ej. `check_password_hash`), reemplazar por comparación directa de texto:
  - Antes: `check_password_hash(row["password"], password_ingresada)`
  - Ahora: `row["password"] == password_ingresada`
