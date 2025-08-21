# api/routes/suppliers.py
from flask import Blueprint, jsonify, request, make_response, render_template_string
from flask_jwt_extended import jwt_required
from api.db.db_config import get_db_connection, DBError
from api.errors import ValidationError, DatabaseError, NotFoundError
from api.utils.roles import admin_required

# PDF opcional
from io import BytesIO
try:
    from xhtml2pdf import pisa
    HAS_PDF = True
except Exception:
    HAS_PDF = False

suppliers_bp = Blueprint("suppliers", __name__)
suppliers_bp.strict_slashes = False

def ok(data=None, status=200):
    payload = {"ok": True}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status

# ============================
# CRUD
# ============================

@suppliers_bp.route("", methods=["GET"])
@jwt_required()
def list_suppliers():
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT id, name, email, phone, contact
            FROM suppliers
            ORDER BY id DESC
        """)
        rows = cur.fetchall()
        cur.close(); conn.close()
        return ok(rows)
    except DBError as e:
        raise DatabaseError("No se pudieron obtener los proveedores", details={"db": str(e)})

@suppliers_bp.route("", methods=["POST"])
@admin_required
def create_supplier():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = data.get("email")
    phone = data.get("phone")
    contact = data.get("contact")

    if not name:
        raise ValidationError("El nombre del proveedor es obligatorio")

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO suppliers (name, email, phone, contact)
            VALUES (%s, %s, %s, %s)
        """, (name, email, phone, contact))
        conn.commit()
        new_id = cur.lastrowid
        cur.close(); conn.close()
        return ok({"id": new_id}, 201)
    except DBError as e:
        raise DatabaseError("No se pudo crear el proveedor", details={"db": str(e)})

@suppliers_bp.route("/<int:supplier_id>", methods=["PUT"])
@admin_required
def update_supplier(supplier_id: int):
    data = request.get_json(silent=True) or {}
    fields, params = [], []

    for k in ("name", "email", "phone", "contact"):
        if k in data:
            if k == "name" and not str(data[k] or "").strip():
                raise ValidationError("El nombre no puede estar vacío")
            fields.append(f"{k}=%s")
            params.append(data[k])

    if not fields:
        raise ValidationError("Nada para actualizar: envía al menos un campo")

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        sql = f"UPDATE suppliers SET {', '.join(fields)} WHERE id=%s"
        params.append(supplier_id)
        cur.execute(sql, tuple(params))
        conn.commit()
        affected = cur.rowcount
        cur.close(); conn.close()
        if affected == 0:
            raise NotFoundError("Proveedor no encontrado")
        return ok({"updated": True})
    except DBError as e:
        raise DatabaseError("No se pudo actualizar el proveedor", details={"db": str(e)})

@suppliers_bp.route("/<int:supplier_id>", methods=["DELETE"])
@admin_required
def delete_supplier(supplier_id: int):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM suppliers WHERE id=%s", (supplier_id,))
        conn.commit()
        affected = cur.rowcount
        cur.close(); conn.close()
        if affected == 0:
            raise NotFoundError("Proveedor no encontrado")
        return ok({"deleted": True})
    except DBError as e:
        raise DatabaseError("No se pudo eliminar el proveedor", details={"db": str(e)})

# ============================
# EXPORTS (solo admin)
# ============================

@suppliers_bp.route("/export/csv", methods=["GET"])
@admin_required
def export_suppliers_csv():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, email, phone, contact FROM suppliers ORDER BY id")
        rows = cur.fetchall()
        cur.close(); conn.close()

        lines = ["id,name,email,phone,contact"]

        def esc(x):
            s = "" if x is None else str(x)
            return '"' + s.replace('"', '""') + '"'

        for r in rows:
            _id, _name, _email, _phone, _contact = r
            lines.append(f'{_id},{esc(_name)},{esc(_email)},{esc(_phone)},{esc(_contact)}')

        csv_data = "\n".join(lines)
        resp = make_response(csv_data)
        resp.headers["Content-Type"] = "text/csv; charset=utf-8"
        resp.headers["Content-Disposition"] = "attachment; filename=proveedores.csv"
        return resp
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@suppliers_bp.route("/export/pdf", methods=["GET"])
@admin_required
def export_suppliers_pdf():
    if not HAS_PDF:
        return jsonify({"ok": False, "error": "xhtml2pdf no está instalado en el entorno"}), 501

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, email, phone, contact FROM suppliers ORDER BY id")
        rows = cur.fetchall()
        cur.close(); conn.close()

        html = render_template_string("""
        <html>
          <head>
            <meta charset="utf-8">
            <style>
              body { font-family: DejaVu Sans, Arial, Helvetica, sans-serif; font-size: 12px; }
              h1 { text-align: center; }
              table { width: 100%; border-collapse: collapse; }
              th, td { border: 1px solid #444; padding: 6px; text-align: left; }
              thead { background: #efefef; }
            </style>
          </head>
          <body>
            <h1>Proveedores</h1>
            <table>
              <thead>
                <tr><th>ID</th><th>Nombre</th><th>Email</th><th>Teléfono</th><th>Contacto</th></tr>
              </thead>
              <tbody>
                {% for r in rows %}
                  <tr>
                    <td>{{ r[0] }}</td>
                    <td>{{ r[1] }}</td>
                    <td>{{ r[2] or "" }}</td>
                    <td>{{ r[3] or "" }}</td>
                    <td>{{ r[4] or "" }}</td>
                  </tr>
                {% endfor %}
              </tbody>
            </table>
          </body>
        </html>
        """, rows=rows)

        pdf_io = BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=pdf_io)
        if pisa_status.err:
            return jsonify({"ok": False, "error": "No se pudo generar el PDF"}), 500

        pdf_io.seek(0)
        resp = make_response(pdf_io.read())
        resp.headers["Content-Type"] = "application/pdf"
        resp.headers["Content-Disposition"] = "inline; filename=proveedores.pdf"
        return resp
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
