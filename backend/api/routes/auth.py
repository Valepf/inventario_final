from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from api.models.users import User
from api.db.db_config import DBError
from datetime import timedelta

auth_bp = Blueprint("auth", __name__)
auth_bp.strict_slashes = False

# ------------------ Helpers de respuesta ------------------
def ok(data=None, status=200):
    payload = {"ok": True}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status

def err(message="Error", code="ERROR", status=400, details=None):
    return jsonify({"ok": False, "error": message, "code": code, "details": details or {}}), status

# ------------------ POST /auth/register (opcional) ------------------
@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Crea un usuario nuevo.
    Body esperado: { "username": str, "password": str, "role": "user"|"admin" }
    *El rol se valida; no se permite otro valor.
    *Se delega a User.register el almacenamiento (idealmente con hash).
    """
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    role     = (data.get("role") or "").strip().lower()

    if not username or not password or role not in {"user", "admin"}:
        return err("Faltan datos o role inválido (use 'user' o 'admin')", "VALIDATION_ERROR", 400)

    try:
        result = User.register({"username": username, "password": password, "role": role})
        return ok(result, 201)
    except DBError as e:
        return err("Error de base de datos", "DB_ERROR", 400, {"db": str(e)})
    except Exception as e:
        return err("Error inesperado", "INTERNAL", 500, {"error": str(e)})

# ------------------ POST /auth/login ------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Autentica un usuario contra la DB.
    Respuesta: { ok:true, data:{ token, role, id } }
    - El 'role' SIEMPRE se toma de la DB (no del body).
    - El token usa identity estilo 'id:role' para compatibilidad con el resto del proyecto.
    """
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return err("Faltan credenciales", "VALIDATION_ERROR", 400)

    try:
        user = User.find_by_username(username)
        # User.check_password debe validar tanto hash como texto plano (según tu implementación)
        if not user or not User.check_password(user["password"], password):
            return err("Credenciales inválidas", "AUTH_ERROR", 401)

        # identidad estilo "id:role" (no aceptar role del cliente)
        identity = f'{user["id"]}:{user["role"]}'
        token = create_access_token(identity=identity, expires_delta=timedelta(hours=8))

        return ok({"token": token, "role": user["role"], "id": user["id"]})
    except DBError as e:
        return err("Falla de base de datos", "DB_ERROR", 500, {"db": str(e)})
    except Exception as e:
        return err("Error inesperado", "INTERNAL", 500, {"error": str(e)})

# ------------------ GET /auth/validate ------------------
@auth_bp.route("/validate", methods=["GET"])
@jwt_required()
def validate():
    """
    Verifica token y devuelve { ok:true, data:{ id, role } }.
    Soporta identity en formato 'id:role'.
    """
    identity = get_jwt_identity()  # esperado: "id:role"
    try:
        user_id, role = identity.split(":")
        return ok({"id": int(user_id), "role": role})
    except Exception as e:
        return err(f"Token inválido: {str(e)}", "AUTH_ERROR", 401)
