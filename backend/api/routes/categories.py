from flask import Blueprint, jsonify, request, make_response, render_template_string
from flask_jwt_extended import jwt_required
from api.db.db_config import get_db_connection, DBError
from api.errors import ValidationError, DatabaseError, NotFoundError
from api.utils.roles import admin_required

# Para PDF
from io import BytesIO
try:
    from xhtml2pdf import pisa
    HAS_PDF = True
except Exception:
    HAS_PDF = False

categories_bp = Blueprint("categories", __name__)
categories_bp.strict_slashes = False

def ok(data=None, status=200):
    payload = {"ok": True}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status

# ----------------------------
# GET /categories (listar)
# ----------------------------
@categories_bp.route("", methods=["GET"])
@jwt_required()
def get_all_categories():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name FROM categories ORDER BY id DESC")
        items = cursor.fetchall()
        cursor.close(); conn.close()
        return ok(items)
    except DBError as e:
        raise DatabaseError("No se pudieron obtener las categorías", details={"db": str(e)})

# ----------------------------
# POST /categories (crear) - admin
# ----------------------------
@categories_bp.route("", methods=["POST"])
@admin_required
def create_category():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()

    if not name:
        raise ValidationError("El nombre de la categoría es obligatorio")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO categories (name) VALUES (%s)", (name,))
        conn.commit()
        category_id = cursor.lastrowid
        cursor.close(); conn.close()
        return ok({"id": category_id}, 201)
    except DBError as e:
        raise DatabaseError("Error al crear categoría", details={"db": str(e)})

# ----------------------------
# PUT /categories/<id> (editar) - admin
# ----------------------------
@categories_bp.route("/<int:category_id>", methods=["PUT"])
@admin_required
def update_category(category_id):
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()

    if not name:
        raise ValidationError("El nombre de la categoría es obligatorio")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE categories SET name=%s WHERE id=%s", (name, category_id))
        conn.commit()
        affected = cursor.rowcount
        cursor.close(); conn.close()
        if affected == 0:
            raise NotFoundError("Categoría no encontrada")
        return ok({"updated": True})
    except DBError as e:
        raise DatabaseError("Error al actualizar categoría", details={"db": str(e)})

# ----------------------------
# DELETE /categories/<id> (eliminar) - admin
# ----------------------------
@categories_bp.route("/<int:category_id>", methods=["DELETE"])
@admin_required
def delete_category(category_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE id=%s", (category_id,))
        conn.commit()
        affected = cursor.rowcount
        cursor.close(); conn.close()
        if affected == 0:
            raise NotFoundError("Categoría no encontrada")
        return ok({"deleted": True})
    except DBError as e:
        raise DatabaseError("Error al eliminar categoría", details={"db": str(e)})

# ============================
# EXPORTS (solo admin)
# ============================
@categories_bp.route("/export/csv", methods=["GET"])
@admin_required
def export_categories_csv():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM categories ORDER BY id")
        rows = cur.fetchall()
        cur.close(); conn.close()

        csv_lines = ["id,name"]
        for r in rows:
            _id = str(r[0])
            _name = str(r[1]).replace('"', '""')
            csv_lines.append(f'{_id},"{_name}"')

        csv_data = "\n".join(csv_lines)
        resp = make_response(csv_data)
        resp.headers["Content-Type"] = "text/csv; charset=utf-8"
        resp.headers["Content-Disposition"] = "attachment; filename=categorias.csv"
        return resp
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@categories_bp.route("/export/pdf", methods=["GET"])
@admin_required
def export_categories_pdf():
    if not HAS_PDF:
        return jsonify({"ok": False, "error": "xhtml2pdf no está instalado en el entorno"}), 501

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM categories ORDER BY id")
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
            <h1>Categorías</h1>
            <table>
              <thead><tr><th>ID</th><th>Nombre</th></tr></thead>
              <tbody>
                {% for r in rows %}
                  <tr><td>{{ r[0] }}</td><td>{{ r[1] }}</td></tr>
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
        resp.headers["Content-Disposition"] = "inline; filename=categorias.pdf"
        return resp
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
