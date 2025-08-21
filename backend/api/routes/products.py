
from flask import Blueprint, jsonify, request, make_response, render_template_string
from flask_jwt_extended import jwt_required
from api.db.db_config import get_db_connection, DBError
from api.errors import ValidationError, DatabaseError, NotFoundError, ConflictError
from api.utils.roles import admin_required

# PDF opcional
from io import BytesIO
try:
    from xhtml2pdf import pisa
    HAS_PDF = True
except Exception:
    HAS_PDF = False

products_bp = Blueprint("products", __name__)
products_bp.strict_slashes = False

def ok(data=None, status=200):
    payload = {"ok": True}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status

# ============================
# Helpers
# ============================

def _coerce_product_payload(data: dict, require_all=True):
    """
    Normaliza y valida el payload de producto.
    require_all=True para POST/PUT completos; False para PATCH (si lo usas).
    """
    if not isinstance(data, dict):
        raise ValidationError("Body JSON inválido")

    name = data.get("name")
    price = data.get("price")
    stock = data.get("stock")
    category_id = data.get("category_id")

    if require_all:
        if not name or price is None or stock is None or category_id is None:
            raise ValidationError("Faltan datos obligatorios: name, price, stock, category_id")

    out = {}
    if name is not None:
        name = str(name).strip()
        if not name:
            raise ValidationError("El nombre no puede estar vacío")
        out["name"] = name

    if price is not None:
        try:
            out["price"] = float(price)
        except Exception:
            raise ValidationError("price debe ser numérico")

    if stock is not None:
        try:
            out["stock"] = int(stock)
        except Exception:
            raise ValidationError("stock debe ser entero")

    if category_id is not None:
        try:
            out["category_id"] = int(category_id)
        except Exception:
            raise ValidationError("category_id debe ser entero")

    return out

def _ensure_category_exists(conn, category_id: int):
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM categories WHERE id=%s", (category_id,))
    row = cur.fetchone()
    cur.close()
    if not row:
        raise NotFoundError(f"La categoría {category_id} no existe")

# ============================
# CRUD
# ============================

@products_bp.route("", methods=["GET"])
@jwt_required()
def get_all_products():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.id, p.name, p.price, p.stock, p.category_id,
                   c.name AS category_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            ORDER BY p.id DESC
        """)
        items = cursor.fetchall()
        cursor.close(); conn.close()
        return ok(items)
    except DBError as e:
        raise DatabaseError("No se pudieron obtener los productos", details={"db": str(e)})

@products_bp.route("", methods=["POST"])
@admin_required
def create_product():
    data = request.get_json(silent=True) or {}
    fields = _coerce_product_payload(data, require_all=True)

    try:
        conn = get_db_connection()
        _ensure_category_exists(conn, fields["category_id"])

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO products (name, price, stock, category_id)
            VALUES (%s, %s, %s, %s)
        """, (fields["name"], fields["price"], fields["stock"], fields["category_id"]))
        conn.commit()
        product_id = cursor.lastrowid
        cursor.close(); conn.close()
        return ok({"id": product_id}, 201)
    except DBError as e:
        msg = str(e)
        if "1062" in msg:
            raise ConflictError("Producto duplicado", details={"db": msg})
        raise DatabaseError("Error al crear producto", details={"db": msg})

@products_bp.route("/<int:product_id>", methods=["PUT"])
@admin_required
def update_product(product_id):
    data = request.get_json(silent=True) or {}
    fields = _coerce_product_payload(data, require_all=True)

    try:
        conn = get_db_connection()
        _ensure_category_exists(conn, fields["category_id"])

        cursor = conn.cursor()
        cursor.execute("""
            UPDATE products
               SET name=%s, price=%s, stock=%s, category_id=%s
             WHERE id=%s
        """, (fields["name"], fields["price"], fields["stock"], fields["category_id"], product_id))
        conn.commit()
        if cursor.rowcount == 0:
            cursor.close(); conn.close()
            raise NotFoundError("Producto no encontrado")
        cursor.close(); conn.close()
        return ok({"updated": True})
    except DBError as e:
        raise DatabaseError("Error al actualizar producto", details={"db": str(e)})

@products_bp.route("/<int:product_id>", methods=["DELETE"])
@admin_required
def delete_product(product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id=%s", (product_id,))
        conn.commit()
        affected = cursor.rowcount
        cursor.close(); conn.close()
        if affected == 0:
            raise NotFoundError("Producto no encontrado")
        return ok({"deleted": True})
    except DBError as e:
        raise DatabaseError("Error al eliminar producto", details={"db": str(e)})

# ============================
# EXPORTS (restringidas a admin)
# ============================

@products_bp.route("/export/csv", methods=["GET"])
@admin_required
def export_products_csv():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id, p.name, p.price, p.stock, p.category_id, c.name AS category_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            ORDER BY p.id
        """)
        rows = cur.fetchall()
        cur.close(); conn.close()

        lines = ["id,name,price,stock,category_id,category_name"]
        for r in rows:
            _id, _name, _price, _stock, _cat_id, _cat_name = r
            def esc(s):
                s = "" if s is None else str(s)
                return '"' + s.replace('"', '""') + '"'
            lines.append(f'{_id},{esc(_name)},{_price},{_stock},{_cat_id},{esc(_cat_name)}')

        csv_data = "\n".join(lines)
        resp = make_response(csv_data)
        resp.headers["Content-Type"] = "text/csv; charset=utf-8"
        resp.headers["Content-Disposition"] = "attachment; filename=productos.csv"
        return resp
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@products_bp.route("/export/pdf", methods=["GET"])
@admin_required
def export_products_pdf():
    if not HAS_PDF:
        return jsonify({"ok": False, "error": "xhtml2pdf no está instalado en el entorno"}), 501
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id, p.name, p.price, p.stock, p.category_id, c.name AS category_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            ORDER BY p.id
        """)
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
            <h1>Productos</h1>
            <table>
              <thead>
                <tr>
                  <th>ID</th><th>Nombre</th><th>Precio</th><th>Stock</th><th>Categoría</th>
                </tr>
              </thead>
              <tbody>
                {% for r in rows %}
                  <tr>
                    <td>{{ r[0] }}</td>
                    <td>{{ r[1] }}</td>
                    <td>{{ "%.2f"|format(r[2]) }}</td>
                    <td>{{ r[3] }}</td>
                    <td>{{ r[5] }}</td>
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
        resp.headers["Content-Disposition"] = "inline; filename=productos.pdf"
        return resp
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
