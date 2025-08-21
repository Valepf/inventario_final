from api.db.db_config import get_db_connection, DBError

class Category:
    schema = {"name": str}

    @classmethod
    def validate(cls, data):
        return data and all(k in data and isinstance(data[k], t) for k, t in cls.schema.items())

    def __init__(self, data):
        # data puede ser tuple o dict (cursor no-dictionary / dictionary)
        if isinstance(data, dict):
            self._id = data.get("id")
            self._name = data.get("name")
            self._description = data.get("description", "")
        else:
            self._id = data[0]
            self._name = data[1]
            self._description = data[2] if len(data) > 2 else ""

    def to_json(self):
        return {"id": self._id, "name": self._name, "description": self._description}

    # ---------- Helpers ----------

    @staticmethod
    def _count_products_by_category(category_id: int) -> int:
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM products WHERE category_id = %s", (category_id,))
            (n,) = cur.fetchone()
            return int(n or 0)
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def _exists_category(category_id: int) -> bool:
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT id FROM categories WHERE id = %s", (category_id,))
            return cur.fetchone() is not None
        finally:
            cur.close()
            conn.close()

    # ---------- CRUD ----------

    @classmethod
    def get_all(cls):
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, name, description FROM categories")
            rows = cur.fetchall()
            return [cls(row).to_json() for row in rows]
        except Exception as e:
            raise DBError(str(e))
        finally:
            cur.close()
            conn.close()

    @classmethod
    def create(cls, data):
        if not cls.validate(data):
            raise DBError("Datos inválidos")
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO categories (name, description) VALUES (%s, %s)",
                (data["name"], data.get("description", ""))
            )
            conn.commit()
            return {"message": "Categoría creada"}
        except Exception as e:
            raise DBError(str(e))
        finally:
            cur.close()
            conn.close()

    @classmethod
    def update(cls, category_id, data):
        if not cls.validate(data):
            raise DBError("Datos inválidos")
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE categories SET name = %s, description = %s WHERE id = %s",
                (data["name"], data.get("description", ""), category_id)
            )
            conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            raise DBError(str(e))
        finally:
            cur.close()
            conn.close()

    @classmethod
    def delete(cls, category_id: int, reassign_to: int | None = None) -> bool:
        """
        Borrado seguro:
        - Si hay productos asociados y no se pasa reassign_to -> BLOQUEA (DBError).
        - Si se pasa reassign_to: valida categoría destino y reasigna antes de eliminar.
        """
        # 1) Validar existencia de la categoría origen
        if not cls._exists_category(category_id):
            raise DBError("Categoría no encontrada")

        # 2) Chequear productos asociados
        n = cls._count_products_by_category(category_id)
        if n > 0 and reassign_to is None:
            raise DBError(f"No se puede eliminar: hay {n} producto(s) asociados. Reasigna primero.")

        # 3) Si hay reasignación, validar destino y hacer UPDATE
        if n > 0 and reassign_to is not None:
            if reassign_to == category_id:
                raise DBError("La categoría de destino no puede ser la misma.")
            if not cls._exists_category(reassign_to):
                raise DBError("Categoría destino inexistente.")

            conn = get_db_connection()
            cur = conn.cursor()
            try:
                # Reasignar productos
                cur.execute(
                    "UPDATE products SET category_id = %s WHERE category_id = %s",
                    (int(reassign_to), int(category_id))
                )
                # Luego eliminar la categoría
                cur.execute("DELETE FROM categories WHERE id = %s", (category_id,))
                if cur.rowcount == 0:
                    conn.rollback()
                    raise DBError("No se pudo eliminar la categoría")
                conn.commit()
                return True
            except Exception as e:
                try:
                    conn.rollback()
                except Exception:
                    pass
                raise DBError(str(e))
            finally:
                cur.close()
                conn.close()

        # 4) Si no hay productos asociados, eliminar directo
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM categories WHERE id = %s", (category_id,))
            conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            raise DBError(str(e))
        finally:
            cur.close()
            conn.close()
