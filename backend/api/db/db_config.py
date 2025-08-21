# db_config.py
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()  # Carga las variables del archivo .env

class DBError(Exception):
    """Clase personalizada para manejar errores de base de datos."""
    pass

def get_db_connection():
    """
    Establece una conexión a la base de datos utilizando mysql.connector.

    Returns:
        connection: Objeto de conexión a la base de datos.
    
    Raises:
        DBError: Si ocurre un error durante la conexión.
    """
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'mi_inventario')
        )
        return connection
    except Error as e:
        raise DBError(f"Error conectando a la base de datos: {str(e)}")
