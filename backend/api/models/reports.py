from api.db.db_config import get_db_connection, DBError

class Report:
    """Clase para generación de reportes."""

    @staticmethod
    def low_stock(threshold=10):
        """
        Genera un reporte de productos con stock por debajo del umbral.
        :param threshold: Umbral de stock (por defecto: 10).
        :return: Lista de productos con bajo stock.
        """
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT id, name, stock FROM products WHERE stock < %s", (threshold,))
            data = cursor.fetchall()
            if data:
                return [{"id": row[0], "name": row[1], "stock": row[2]} for row in data]
            return []
        except Exception as e:
            raise DBError(f"Error generando el reporte de bajo stock: {str(e)}")
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def orders_history():
        """
        Genera un reporte del historial de órdenes.
        :return: Lista de órdenes con detalles.
        """
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            query = """
                SELECT o.id, p.name AS product, o.quantity, o.order_date, o.status
                FROM orders o
                JOIN products p ON o.product_id = p.id
                ORDER BY o.order_date DESC
            """
            cursor.execute(query)
            data = cursor.fetchall()
            if data:
                return [
                    {
                        "id": row[0],
                        "product": row[1],
                        "quantity": row[2],
                        "order_date": str(row[3]),
                        "status": row[4]
                    }
                    for row in data
                ]
            return []
        except Exception as e:
            raise DBError(f"Error generando el historial de órdenes: {str(e)}")
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def current_inventory():
        """
        Genera un reporte del inventario actual.
        :return: Lista de productos con valores totales.
        """
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            query = """
                SELECT id, name, stock, price, (stock * price) AS total_value
                FROM products
            """
            cursor.execute(query)
            data = cursor.fetchall()
            if data:
                return [
                    {
                        "id": row[0],
                        "name": row[1],
                        "stock": row[2],
                        "price": float(row[3]),
                        "total_value": float(row[4])
                    }
                    for row in data
                ]
            return []
        except Exception as e:
            raise DBError(f"Error generando el reporte de inventario: {str(e)}")
        finally:
            cursor.close()
            connection.close()
