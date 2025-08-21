# api/routes/users.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from werkzeug.security import generate_password_hash
from api.db.db_config import get_db_connection, DBError
from api.errors import ValidationError, DatabaseError, NotFoundError, ConflictError
from api.utils.roles import admin_required

users_bp = Blueprint("users", __name__)
users_bp.strict_slashes = False

# ---------- helpers de respuesta ----------
def ok(data=None, status=200):
    payload = {"ok": True}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status

def _norm_role(role: str):
    r = (role or "").strip().lower()
    # compat: mapear "general" -> "user"
    if r == "general":
        r = "user"
    if r not in {"user", "admin"}:
        raise ValidationError("role inválido (use 'user' o 'admin')")
    return r

# ---------- GET /users (solo admin) ----------
@users_bp.route("", methods=["GET"])
@admin_required
def list_users():
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        # asumimos que ya agregaste created_at a la tabla (como hicimos antes)
        cur.execute("SELECT id, username, role, created_at FROM users ORDER BY id DESC")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return ok(rows)
    except DBError as e:
        raise DatabaseError("No se pudieron obtener los usuarios", details={"db": str(e)})

# ---------- POST /users (solo admin) ----------
@users_bp.route("", methods=["POST"])
@admin_required
def create_user():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    role     = _norm_role(data.get("role"))

    if not username:
        raise ValidationError("username es obligatorio")
    if not password:
        raise ValidationError("password es obligatorio")

    # hashear con scrypt para ser compatibles con tus datos existentes
    pwd_hash = generate_password_hash(password, method="scrypt")

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (username, password, role, created_at)
            VALUES (%s, %s, %s, NOW())
        """, (username, pwd_hash, role))
        conn.commit()
        new_id = cur.lastrowid
        cur.close(); conn.close()
        return ok({"id": new_id}, 201)
    except DBError as e:
        msg = str(e)
        if "1062" in msg or "Duplicate" in msg:
            raise ConflictError("El username ya existe", details={"db": msg})
        raise DatabaseError("No se pudo crear el usuario", details={"db": msg})

# ---------- PUT /users/<id> (solo admin) ----------
@users_bp.route("/<int:user_id>", methods=["PUT"])
@admin_required
def update_user(user_id: int):
    data = request.get_json(silent=True) or {}

    fields = []
    params = []

    if "username" in data:
        username = (data.get("username") or "").strip()
        if not username:
            raise ValidationError("username no puede estar vacío")
        fields.append("username=%s")
        params.append(username)

    if "role" in data:
        role = _norm_role(data.get("role"))
        fields.append("role=%s")
        params.append(role)

    if "password" in data:
        pwd = (data.get("password") or "").strip()
        if not pwd:
            raise ValidationError("password no puede ser vacío si se envía")
        pwd_hash = generate_password_hash(pwd, method="scrypt")
        fields.append("password=%s")
        params.append(pwd_hash)

    if not fields:
        raise ValidationError("Nada para actualizar: envía username, role o password")

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        sql = f"UPDATE users SET {', '.join(fields)} WHERE id=%s"
        params.append(user_id)
        cur.execute(sql, tuple(params))
        conn.commit()
        affected = cur.rowcount
        cur.close(); conn.close()
        if affected == 0:
            raise NotFoundError("Usuario no encontrado")
        return ok({"updated": True})
    except DBError as e:
        msg = str(e)
        if "1062" in msg or "Duplicate" in msg:
            raise ConflictError("El username ya existe", details={"db": msg})
        raise DatabaseError("No se pudo actualizar el usuario", details={"db": msg})

# ---------- DELETE /users/<id> (solo admin) ----------
@users_bp.route("/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id: int):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
        conn.commit()
        affected = cur.rowcount
        cur.close(); conn.close()
        if affected == 0:
            raise NotFoundError("Usuario no encontrado")
        return ok({"deleted": True})
    except DBError as e:
        raise DatabaseError("No se pudo eliminar el usuario", details={"db": str(e)})
