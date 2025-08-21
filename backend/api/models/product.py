from api.db.db_config import get_db_connection, DBError

class Product:
    """
    Modelo de productos con soporte de proveedor (supplier_id).
    Adaptado a MySQL (mysql-connector): usar placeholders %s.
    """

    # price acepta int/float; supplier_id puede ser None
    schema = {
        "name": str,
        "price": (int, float),
        "stock": int,
        "category_id": int,
        "supplier_id": (int, type(None))
    }

    # ---------- Validación ----------

    @classmethod
    def validate(cls, data, partial: bool = False) -> bool:
        """Valida estructura y tipos permitiendo parcial en updates."""
        if not isinstance(data, dict) or not data:
            return False

        keys = data.keys() if partial else cls.schema.keys()
        for k in keys:
            if k not in cls.schema:
                
                continue
            exp = cls.schema[k]
            if k not in data:
                if partial:
                    continue
                return False

            v = data[k]
            
            if exp in (int, (int, float)) or exp == (int, float):
                if v is None:
                    return False
                try:
                    float(v) if k == "price" else int(v)
                except (ValueError, TypeError):
                    return False
            else:
                if isinstance(exp, tuple):
                    if not isinstance(v, exp):
                        return False
                else:
                    if not isinstance(v, exp):
                        return False
        return True

    # ---------- Consultas (READ) ----------

    @classmethod
    def get_all_with_category_supplier(cls):
        """Lista productos con nombres de categoría y proveedor (LEFT JOIN)."""
        try:
            conn = get_db_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute(
                """
                SELECT p.id, p.name, p.price, p.stock, p.category_id, p.supplier_id,
                       c.name AS category_name,
                       s.name AS supplier_name
                FROM products p
                LEFT JOIN categories c ON c.id = p.category_id
                LEFT JOIN suppliers s ON s.id = p.supplier_id
                ORDER BY p.id DESC
                """
            )
            rows = cur.fetchall()
            conn.close()
            return rows
        except Exception as e:
            raise DBError(f"Error obteniendo productos: {str(e)}")

    @classmethod
    def get_by_id_with_category_supplier(cls, product_id: int):
        """Obtiene un producto por id con category_name y supplier_name."""
        try:
            conn = get_db_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute(
                """
                SELECT p.id, p.name, p.price, p.stock, p.category_id, p.supplier_id,
                       c.name AS category_name,
                       s.name AS supplier_name
                FROM products p
                LEFT JOIN categories c ON c.id = p.category_id
                LEFT JOIN suppliers s ON s.id = p.supplier_id
                WHERE p.id = %s
                """,
                (product_id,)
            )
            row = cur.fetchone()
            conn.close()
            return row
        except Exception as e:
            raise DBError(f"Error obteniendo producto: {str(e)}")

    # ---------- Mutaciones (CREATE/UPDATE/DELETE) ----------

    @classmethod
    def create(cls, data: dict) -> int:
        """
        Crea un producto. Devuelve el id nuevo.
        Valida existencia de category_id y supplier_id (si viene).
        """
        if not cls.validate(data):
            raise DBError("Datos inválidos para crear producto")

        name = data["name"].strip()
        price = float(data["price"])
        stock = int(data["stock"])
        category_id = int(data["category_id"])
        supplier_id = data.get("supplier_id")
        supplier_id = int(supplier_id) if supplier_id is not None else None

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Validar categoría
            cur.execute("SELECT id FROM categories WHERE id = %s", (category_id,))
            if not cur.fetchone():
                conn.close()
                raise DBError(f"category_id {category_id} no existe")

            # Validar proveedor (si viene)
            if supplier_id is not None:
                cur.execute("SELECT id FROM suppliers WHERE id = %s", (supplier_id,))
                if not cur.fetchone():
                    conn.close()
                    raise DBError(f"supplier_id {supplier_id} no existe")

            cur.execute(
                """
                INSERT INTO products (name, price, stock, category_id, supplier_id)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (name, price, stock, category_id, supplier_id)
            )
            new_id = cur.lastrowid
            conn.commit()
            conn.close()
            return new_id
        except DBError:
            raise
        except Exception as e:
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
            raise DBError(f"Error creando producto: {str(e)}")

    @classmethod
    def update(cls, product_id: int, data: dict) -> int:
        """
        Actualiza campos permitidos. Devuelve cantidad de filas afectadas.
        Valida category_id/supplier_id si vienen en el payload.
        """
        if not isinstance(data, dict) or not data:
            raise DBError("No hay datos para actualizar")

        if not cls.validate(data, partial=True):
            raise DBError("Datos inválidos para actualizar producto")

        allowed = ("name", "price", "stock", "category_id", "supplier_id")
        sets, params = [], []

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            if "category_id" in data and data["category_id"] is not None:
                cid = int(data["category_id"])
                cur.execute("SELECT id FROM categories WHERE id = %s", (cid,))
                if not cur.fetchone():
                    conn.close()
                    raise DBError(f"category_id {cid} no existe")

            if "supplier_id" in data:
                sid = data["supplier_id"]
                if sid is not None:
                    sid = int(sid)
                    cur.execute("SELECT id FROM suppliers WHERE id = %s", (sid,))
                    if not cur.fetchone():
                        conn.close()
                        raise DBError(f"supplier_id {sid} no existe")

            for k in allowed:
                if k in data:
                    v = data[k]
                    if k in ("price",) and v is not None:
                        v = float(v)
                    if k in ("stock", "category_id") and v is not None:
                        v = int(v)
                    if k == "supplier_id" and v is not None:
                        v = int(v)
                    sets.append(f"{k} = %s")
                    params.append(v)

            if not sets:
                conn.close()
                raise DBError("Ningún campo válido para actualizar")

            params.append(product_id)
            cur.execute(f"UPDATE products SET {', '.join(sets)} WHERE id = %s", tuple(params))
            affected = cur.rowcount
            if affected == 0:
                conn.close()
                raise DBError("Producto no encontrado")
            conn.commit()
            conn.close()
            return affected
        except DBError:
            raise
        except Exception as e:
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
            raise DBError(f"Error actualizando producto: {str(e)}")

    @classmethod
    def delete(cls, product_id: int):
        """Elimina un producto por id."""
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
            if cur.rowcount == 0:
                conn.close()
                raise DBError("Producto no encontrado")
            conn.commit()
            conn.close()
        except DBError:
            raise
        except Exception as e:
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
            raise DBError(f"Error borrando producto: {str(e)}")

    # ---------- (Opcional) Filtro por usuario ----------

    @classmethod
    def get_products_by_user(cls, user_id: int):
        """
        Úsalo sólo si tu tabla products tiene columna user_id.
        """
        try:
            conn = get_db_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute(
                """
                SELECT id, name, price, stock, category_id, supplier_id
                FROM products
                WHERE user_id = %s
                ORDER BY id DESC
                """,
                (user_id,)
            )
            rows = cur.fetchall()
            conn.close()
            return rows
        except Exception as e:
            raise DBError(f"Error obteniendo productos del usuario: {str(e)}")
