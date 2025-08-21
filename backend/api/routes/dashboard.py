from flask import Blueprint, jsonify
from api.db.db_config import get_db_connection, DBError
from api.utils.security import token_required

dashboard_bp = Blueprint("dashboard", __name__)
dashboard_bp.strict_slashes = False

def ok(data=None, status=200):
    payload = {"ok": True}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status

def err(message="Error interno del servidor", code="INTERNAL_ERROR", status=500, details=None):
    return jsonify({"ok": False, "error": message, "code": code, "details": details or {}}), status

@dashboard_bp.route("/metrics", methods=["GET"])
@token_required
def metrics(*args, **kwargs):
    """
    Devuelve:
      {
        "products": int,
        "categories": int,
        "suppliers": int,
        "orders_today": int,
        "low_stock": int        # productos con stock <= 5
      }
    """
    try:
        connection = get_db_connection()
        cur = connection.cursor(dictionary=True)

        cur.execute("SELECT COUNT(*) AS c FROM products")
        products = (cur.fetchone() or {}).get("c", 0)

        cur.execute("SELECT COUNT(*) AS c FROM categories")
        categories = (cur.fetchone() or {}).get("c", 0)

        cur.execute("SELECT COUNT(*) AS c FROM suppliers")
        suppliers = (cur.fetchone() or {}).get("c", 0)

        # Órdenes de HOY (por order_date)
        cur.execute("""
            SELECT COUNT(*) AS c
            FROM orders
            WHERE order_date >= CURDATE()
              AND order_date <  DATE_ADD(CURDATE(), INTERVAL 1 DAY)
        """)
        orders_today = (cur.fetchone() or {}).get("c", 0)

        # Bajo stock (umbral 5)
        cur.execute("SELECT COUNT(*) AS c FROM products WHERE stock <= 5")
        low_stock = (cur.fetchone() or {}).get("c", 0)

        cur.close()
        connection.close()

        return ok({
            "products": products,
            "categories": categories,
            "suppliers": suppliers,
            "orders_today": orders_today,
            "low_stock": low_stock
        })
    except DBError as e:
        return err("No se pudieron obtener métricas", details={"db": str(e)})
    except Exception as e:
        return err(str(e))
