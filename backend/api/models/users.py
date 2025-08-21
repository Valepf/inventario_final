from api.db.db_config import get_db_connection, DBError
from werkzeug.security import check_password_hash, generate_password_hash

class User:
    schema = {"username": str, "password": str, "role": str}

    @classmethod
    def validate(cls, data):
        if not data or not isinstance(data, dict):
            return False
        for key in cls.schema:
            if key not in data or not isinstance(data[key], cls.schema[key]):
                return False
        return True

    @classmethod
    def register(cls, data):
        if not cls.validate(data):
            raise DBError("Campos inválidos")

        # 👉 Guarda SIEMPRE hasheado (compatible con el seeder scrypt)
        hashed = cls.hash_password(data["password"])

        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (data["username"], hashed, data["role"])
            )
            connection.commit()
            return {"message": "Usuario registrado exitosamente"}
        except Exception as e:
            raise DBError(str(e))
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def hash_password(password: str) -> str:
        # El seeder usa scrypt → usamos scrypt para ser consistentes
        return generate_password_hash(password, method="scrypt")

    @staticmethod
    def check_password(stored_password: str, input_password: str) -> bool:
        """
        Valida hash (scrypt/pbkdf2/…) si corresponde; si no, compara plano.
        Así funcionan usuarios del seeder (hash) y los antiguos (plano).
        """
        if not isinstance(stored_password, str):
            return False
        # Si tiene pinta de hash de Werkzeug:
        if stored_password.startswith(("scrypt:", "pbkdf2:", "argon2:")):
            try:
                return check_password_hash(stored_password, input_password)
            except Exception:
                return False
        # Caso legacy texto plano
        return stored_password == input_password

    @classmethod
    def find_by_username(cls, username):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id, username, role, password FROM users WHERE username = %s",
                (username,)
            )
            user = cursor.fetchone()
            return user
        except Exception as e:
            raise DBError(str(e))
        finally:
            cursor.close()
            connection.close()
