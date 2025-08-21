from api.db.db_config import get_db_connection, DBError

class Order():
    schema = {
        "product_id": int,
        "quantity": int,
        "status": str
    }

    @classmethod
    def validate(cls, data):
        """Valida la estructura de los datos de entrada."""
        if not data or not isinstance(data, dict):
            return False
        for key in cls.schema:
            if key not in data or not isinstance(data[key], cls.schema[key]):
                return False
        return True

    def __init__(self, data):
        """Constructor basado en las columnas de la base de datos."""
        self._id = data[0]
        self._product_id = data[1]
        self._quantity = data[2]
        self._status = data[3]
        self._user_id = data[4]

    def to_json(self):
        """Convierte el objeto en JSON."""
        return {
            "id": self._id,
            "product_id": self._product_id,
            "quantity": self._quantity,
            "status": self._status,
            "user_id": self._user_id
        }

    @staticmethod
    def get_all_orders():
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM orders")
            result = cursor.fetchall()
            cursor.close()
            connection.close()
            return [Order(row).to_json() for row in result]
        except Exception as e:
            raise DBError(f"Error al obtener órdenes: {str(e)}")

    @staticmethod
    def create_order(data):
        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            sql = """
                INSERT INTO orders (product_id, quantity, order_date, status)
                VALUES (%s, %s, %s, %s)
            """
            values = (
                data["product_id"],
                data["quantity"],
                data["order_date"],
                data["status"]
            )

            cursor.execute(sql, values)
            connection.commit()
            cursor.close()
            connection.close()
            return {"message": "Orden creada correctamente"}
        except Exception as e:
            raise DBError(f"Error al crear la orden: {str(e)}")

    @staticmethod
    def update_order(order_id, data):
        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            sql = """
                UPDATE orders
                SET product_id = %s, quantity = %s, status = %s
                WHERE id = %s
            """
            values = (
                data["product_id"],
                data["quantity"],
                data["status"],
                order_id
            )

            cursor.execute(sql, values)
            connection.commit()
            cursor.close()
            connection.close()
            return {"message": "Orden actualizada correctamente"}
        except Exception as e:
            raise DBError(f"Error al actualizar la orden: {str(e)}")

    @staticmethod
    def delete_order(order_id):
        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            sql = "DELETE FROM orders WHERE id = %s"
            cursor.execute(sql, (order_id,))
            connection.commit()
            cursor.close()
            connection.close()
            return {"message": "Orden eliminada correctamente"}
        except Exception as e:
            raise DBError(f"Error al eliminar la orden: {str(e)}")
