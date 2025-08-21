# api/models/supplier.py

from api.db.db_config import get_db_connection, DBError

class Supplier:
    """
    Modelo para representar un proveedor.
    """

    @staticmethod
    def get_all():
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM suppliers")
            data = cursor.fetchall()
            return data
        except Exception as e:
            raise DBError(str(e))
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def create(name, contact):
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("INSERT INTO suppliers (name, contact) VALUES (%s, %s)", (name, contact))
            connection.commit()
        except Exception as e:
            raise DBError(str(e))
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def delete_by_id(supplier_id):
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("DELETE FROM suppliers WHERE id = %s", (supplier_id,))
            connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            raise DBError(str(e))
        finally:
            cursor.close()
            connection.close()
