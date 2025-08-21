# api/utils/security.py
from functools import wraps
from flask import request, jsonify, Blueprint, render_template, current_app
from flask_jwt_extended import (
    verify_jwt_in_request,
    get_jwt_identity,
    create_access_token,
)
from datetime import timedelta

def _err(message="No autorizado", code="AUTH_ERROR", status=401, details=None):
    return jsonify({"ok": False, "error": message, "code": code, "details": details or {}}), status

def token_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            ident = get_jwt_identity()
            # Soportar identity como dict {"id":..., "role":...} o "id:role"
            if isinstance(ident, dict):
                user_id = ident.get("id")
                role = ident.get("role")
            else:
                user_id_str, role = (ident or "").split(":")
                user_id = int(user_id_str)
            kwargs["user_id"] = user_id
            kwargs["role"] = role
            return fn(*args, **kwargs)
        except Exception as e:
            return _err(f"No autorizado: {str(e)}", "AUTH_ERROR", 401)
    return wrapper

security_bp = Blueprint("security", __name__, template_folder="../../templates")

@security_bp.route("/login", methods=["GET"])
def login_page():
    # Renderiza templates/login.html
    return render_template("login.html")

@security_bp.route("/login", methods=["POST"])
def login_api():
    """
    Endpoint simple de autenticación.
    - Espera JSON: { "username": "...", "password": "...", "role": "admin|general" }
    - Genera un JWT con identity {"id": <int>, "role": <str>}
    NOTA: Aquí lo dejo en modo DEMO (sin hash y sin DB). Adaptá a tu tabla de usuarios si la tenés.
    """
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    role = (data.get("role") or "").strip().lower()

    if role not in ("admin", "general"):
        return _err("Rol inválido", "ROLE_INVALID", 400, {"role": role})

    if not username or not password:
        return _err("Usuario y contraseña son obligatorios", "MISSING_FIELDS", 400)

    # 🚧 DEMO: Autenticar sin DB. Acepta cualquier user/pass no vacíos.
    # Si tenés tabla 'users', reemplazá este bloque por tu validación real.
    user_id = 1 if role == "admin" else 2

    # Configurar expiración (por ej. 8 horas)
    expires = timedelta(hours=8)
    # Identity como dict (tu decorador ya soporta ambos formatos)
    identity = {"id": user_id, "role": role, "username": username}
    token = create_access_token(identity=identity, expires_delta=expires)

    return jsonify({"ok": True, "token": token, "role": role, "user_id": user_id}), 200
