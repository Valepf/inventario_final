# api/routes/orders.py
from flask import Blueprint, jsonify, request
from api.db.db_config import get_db_connection, DBError
from api.utils.security import token_required       # autenticado (inyecta user_id en kwargs)
from api.utils.roles import admin_required          # SOLO admin (usa JWT)

orders_bp = Blueprint("orders", __name__)
orders_bp.strict_slashes = False  # evitamos 308 por la barra final

# Helpers de respuesta unificada
def ok(data=None, status=200):
    payload = {"ok": True}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status

def err(message="Error interno del servidor", code="INTERNAL_ERROR", status=500, details=None):
    return jsonify({
        "ok": False,
        "error": message,
        "code": code,
        "details": details or {}
    }), status

# --------- Utils de validación/simple ---------
def _to_int(val, default=None):
    try:
        return int(val)
    except Exception:
        return default

def _status_norm(s):
    return (s or "").strip().lower()

VALID_STATUS = {"pending", "received", "completed", "cancelled", "canceled"}

# --------- GET /orders (lista con filtros) ---------
@orders_bp.route("", methods=["GET"])
@token_required
def list_orders(*args, **kwargs):
    """
    Filtros opcionales:
      ?from=YYYY-MM-DD
      ?to=YYYY-MM-DD
      ?status=pending|received|completed|cancelled
      ?product_id=ID
    """
    try:
        q_from = request.args.get("from")
        q_to = request.args.get("to")
        q_status = _status_norm(request.args.get("status"))
        q_product = _to_int(request.args.get("product_id"))

        connection = get_db_connection()
        cur = connection.cursor(dictionary=True)

        where = []
        params = []

        if q_from:
            where.append("o.order_date >= %s")
            params.append(f"{q_from} 00:00:00")
        if q_to:
            where.append("o.order_date <= %s")
            params.append(f"{q_to} 23:59:59")
        if q_status:
            where.append("LOWER(o.status) = %s")
            params.append(q_status)
        if q_product is not None:
            where.append("o.product_id = %s")
            params.append(q_product)

        sql = """
            SELECT o.id, o.product_id, p.name AS product_name,
                   o.quantity, o.status,
                   o.order_date, o.receipt_date,
                   o.user_id
            FROM orders o
            JOIN products p ON p.id = o.product_id
        """
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY o.order_date DESC, o.id DESC"

        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
        cur.close()
        connection.close()
        return ok(rows)
    except DBError as e:
        return err("No se pudieron listar las órdenes", details={"db": str(e)})
    except Exception as e:
        return err(str(e))

# --------- GET /orders/<id> (detalle) ---------
@orders_bp.route("/<int:order_id>", methods=["GET"])
@token_required
def get_order(order_id, *args, **kwargs):
    try:
        connection = get_db_connection()
        cur = connection.cursor(dictionary=True)
        cur.execute("""
            SELECT o.id, o.product_id, p.name AS product_name,
                   o.quantity, o.status,
                   o.order_date, o.receipt_date,
                   o.user_id
            FROM orders o
            JOIN products p ON p.id = o.product_id
            WHERE o.id = %s
        """, (order_id,))
        row = cur.fetchone()
        cur.close()
        connection.close()
        if not row:
            return err("Orden no encontrada", code="NOT_FOUND", status=404)
        return ok(row)
    except DBError as e:
        return err("No se pudo obtener la orden", details={"db": str(e)})

# --------- POST /orders (crear) ---------
@orders_bp.route("", methods=["POST"])
@token_required
def create_order(*args, **kwargs):
    """
    Body esperado (JSON):
      {
        "product_id": int,   (requerido)
        "quantity":   int>0, (requerido)
        "status":     str    (opcional, default 'pending')
      }
    * Cualquier autenticado puede crear.
    """
    try:
        data = request.get_json(silent=True) or {}
        product_id = _to_int(data.get("product_id"))
        quantity = _to_int(data.get("quantity"))
        status = _status_norm(data.get("status") or "pending")
        user_id = kwargs.get("user_id")  # del token_required

        if product_id is None:
            return err("product_id es requerido", code="VALIDATION_ERROR", status=400)
        if quantity is None or quantity <= 0:
            return err("quantity debe ser entero > 0", code="VALIDATION_ERROR", status=400)
        if status and status not in VALID_STATUS:
            return err(f"status inválido: {status}", code="VALIDATION_ERROR", status=400)

        connection = get_db_connection()
        cur = connection.cursor(dictionary=True)

        # verificar existencia del producto
        cur.execute("SELECT id FROM products WHERE id = %s", (product_id,))
        if not cur.fetchone():
            cur.close()
            connection.close()
            return err("Producto inexistente", code="VALIDATION_ERROR", status=400)

        # insertar orden con order_date = NOW()
        cur.execute(
            """
            INSERT INTO orders (product_id, quantity, status, order_date, user_id)
            VALUES (%s, %s, %s, NOW(), %s)
            """,
            (product_id, quantity, status or "pending", user_id)
        )
        new_id = cur.lastrowid
        connection.commit()

        # devolver registro creado
        cur.execute("""
            SELECT o.id, o.product_id, p.name AS product_name,
                   o.quantity, o.status,
                   o.order_date, o.receipt_date,
                   o.user_id
            FROM orders o
            JOIN products p ON p.id = o.product_id
            WHERE o.id = %s
        """, (new_id,))
        row = cur.fetchone()
        cur.close()
        connection.close()
        return ok(row, status=201)
    except DBError as e:
        return err("No se pudo crear la orden", details={"db": str(e)})
    except Exception as e:
        return err(str(e))

# --------- PUT /orders/<id> (actualizar) ---------
@orders_bp.route("/<int:order_id>", methods=["PUT"])
@admin_required
def update_order(order_id, *args, **kwargs):
    """
    SOLO ADMIN.
    Campos aceptados: quantity (int>0), status (enum), receipt_date (YYYY-MM-DD HH:MM:SS)
    Regla: si status pasa a 'received'/'completed' y NO mandan receipt_date, se fija NOW().
    """
    try:
        data = request.get_json(silent=True) or {}

        fields = []
        params = []

        if "quantity" in data:
            q = _to_int(data.get("quantity"))
            if q is None or q <= 0:
                return err("quantity debe ser entero > 0", code="VALIDATION_ERROR", status=400)
            fields.append("quantity = %s")
            params.append(q)

        set_receipt_now = False
        if "status" in data:
            st = _status_norm(data.get("status"))
            if st and st not in VALID_STATUS:
                return err(f"status inválido: {st}", code="VALIDATION_ERROR", status=400)
            fields.append("status = %s")
            params.append(st)
            if st in {"received", "completed"} and "receipt_date" not in data:
                set_receipt_now = True

        if "receipt_date" in data:
            rd = data.get("receipt_date")
            if rd is None:
                fields.append("receipt_date = NULL")
            else:
                fields.append("receipt_date = %s")
                params.append(str(rd))

        if set_receipt_now:
            fields.append("receipt_date = NOW()")  # literal SQL

        if not fields:
            return err("No hay campos válidos para actualizar", code="VALIDATION_ERROR", status=400)

        connection = get_db_connection()
        cur = connection.cursor(dictionary=True)

        # verificar existencia
        cur.execute("SELECT id FROM orders WHERE id = %s", (order_id,))
        if not cur.fetchone():
            cur.close()
            connection.close()
            return err("Orden no encontrada", code="NOT_FOUND", status=404)

        sql = f"UPDATE orders SET {', '.join(fields)} WHERE id = %s"
        params.append(order_id)
        cur.execute(sql, tuple(params))
        connection.commit()

        # devolver actualizado
        cur.execute("""
            SELECT o.id, o.product_id, p.name AS product_name,
                   o.quantity, o.status,
                   o.order_date, o.receipt_date,
                   o.user_id
            FROM orders o
            JOIN products p ON p.id = o.product_id
            WHERE o.id = %s
        """, (order_id,))
        row = cur.fetchone()
        cur.close()
        connection.close()
        return ok(row)
    except DBError as e:
        return err("No se pudo actualizar la orden", details={"db": str(e)})
    except Exception as e:
        return err(str(e))

# --------- DELETE /orders/<id> (eliminar) ---------
@orders_bp.route("/<int:order_id>", methods=["DELETE"])
@admin_required
def delete_order(order_id, *args, **kwargs):
    """SOLO ADMIN."""
    try:
        connection = get_db_connection()
        cur = connection.cursor()
        cur.execute("DELETE FROM orders WHERE id = %s", (order_id,))
        affected = cur.rowcount
        connection.commit()
        cur.close()
        connection.close()
        if affected == 0:
            return err("Orden no encontrada", code="NOT_FOUND", status=404)
        return ok({"deleted": order_id})
    except DBError as e:
        return err("No se pudo eliminar la orden", details={"db": str(e)})
    except Exception as e:
        return err(str(e))
