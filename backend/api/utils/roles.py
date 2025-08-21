# api/utils/roles.py
from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

def _extract_role():
    ident = get_jwt_identity()
    # Soporta ambos formatos que vi en tu proyecto:
    # - str "id:role"
    # - dict {"id": ..., "role": ...}
    if isinstance(ident, dict):
        return ident.get("role")
    if isinstance(ident, str):
        parts = ident.split(":", 1)
        if len(parts) == 2:
            return parts[1]
    return None

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        role = _extract_role()
        if role != "admin":
            return jsonify({"ok": False, "error": "No autorizado", "code": "FORBIDDEN"}), 403
        return fn(*args, **kwargs)
    return wrapper
