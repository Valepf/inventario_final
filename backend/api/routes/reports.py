# api/routes/reports.py
from flask import Blueprint, jsonify, request, Response
from api.db.db_config import get_db_connection, DBError
from api.utils.security import token_required

import csv
import io
from datetime import date

reports_bp = Blueprint("reports", __name__)
reports_bp.strict_slashes = False

# ----------------- Helpers de respuesta -----------------
def ok(data=None, status=200):
    payload = {"ok": True}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status

def err(message="Error interno del servidor", code="INTERNAL_ERROR", status=500, details=None):
    return jsonify({"ok": False, "error": message, "code": code, "details": details or {}}), status

# ----------------- Consultas base (reutilizables) -----------------
def _q_stock_by_category(cur):
    cur.execute("""
        SELECT c.name AS category,
               COALESCE(SUM(p.stock), 0) AS total_stock
        FROM categories c
        LEFT JOIN products p ON p.category_id = c.id
        GROUP BY c.id, c.name
        ORDER BY c.name
    """)
    return cur.fetchall()

def _q_orders_history(cur):
    # Intento con CTE (MySQL 8). Si falla, fallback.
    try:
        cur.execute("""
            WITH RECURSIVE months AS (
                SELECT DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 11 MONTH), '%Y-%m-01') AS m
                UNION ALL
                SELECT DATE_ADD(m, INTERVAL 1 MONTH) FROM months
                WHERE m < DATE_FORMAT(CURDATE(), '%Y-%m-01')
            )
            SELECT DATE_FORMAT(m, '%Y-%m') AS month,
                   COALESCE(COUNT(o.id), 0) AS count
            FROM months
            LEFT JOIN orders o
                   ON DATE_FORMAT(o.order_date, '%Y-%m-01') = m
            GROUP BY m
            ORDER BY m
        """)
        return cur.fetchall()
    except Exception:
        cur.execute("""
            SELECT DATE_FORMAT(order_date, '%Y-%m') AS month,
                   COUNT(*) AS count
            FROM orders
            WHERE order_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
            GROUP BY DATE_FORMAT(order_date, '%Y-%m')
            ORDER BY month
        """)
        return cur.fetchall()

def _q_low_stock(cur, threshold: int):
    cur.execute("""
        SELECT p.id, p.name, p.stock, c.name AS category
        FROM products p
        LEFT JOIN categories c ON c.id = p.category_id
        WHERE p.stock <= %s
        ORDER BY p.stock ASC, p.name ASC
    """, (threshold,))
    return cur.fetchall()

# ----------------- Endpoints JSON usados por tu dashboard/reports.js -----------------
@reports_bp.route("/stock-by-category", methods=["GET"])
@token_required
def stock_by_category(*args, **kwargs):
    try:
        con = get_db_connection(); cur = con.cursor(dictionary=True)
        rows = _q_stock_by_category(cur)
        cur.close(); con.close()
        return ok(rows)
    except DBError as e:
        return err("No se pudo obtener stock por categoría", details={"db": str(e)})
    except Exception as e:
        return err(str(e))

@reports_bp.route("/orders-history", methods=["GET"])
@token_required
def orders_history(*args, **kwargs):
    try:
        con = get_db_connection(); cur = con.cursor(dictionary=True)
        rows = _q_orders_history(cur)
        cur.close(); con.close()
        return ok(rows)
    except DBError as e:
        return err("No se pudo obtener historial de órdenes", details={"db": str(e)})
    except Exception as e:
        return err(str(e))

@reports_bp.route("/low-stock", methods=["GET"])
@token_required
def low_stock(*args, **kwargs):
    """
    ?threshold=5 (default)
    Devuelve productos con stock <= threshold
    """
    try:
        thr = request.args.get("threshold", "5")
        try:
            thr_int = int(thr)
        except Exception:
            thr_int = 5

        con = get_db_connection(); cur = con.cursor(dictionary=True)
        rows = _q_low_stock(cur, thr_int)
        cur.close(); con.close()
        return ok(rows)
    except DBError as e:
        return err("No se pudo obtener bajo stock", details={"db": str(e)})
    except Exception as e:
        return err(str(e))

# ----------------- Helpers de exportación -----------------
def _csv_response(filename: str, header: list, rows: list, keymap: list):
    """
    header: títulos de columnas
    rows: lista de dicts
    keymap: en qué orden tomar cada clave del dict (misma longitud que header)
    """
    sio = io.StringIO()
    writer = csv.writer(sio)
    writer.writerow(header)
    for r in rows:
        writer.writerow([r.get(k, "") for k in keymap])

    out = sio.getvalue()
    return Response(
        out,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )

def _pdf_response_simple(title: str, columns: list, rows: list, filename: str):
    """
    Genera PDF con reportlab si está instalado. Si no, devuelve 501 con instrucción.
    columns: títulos
    rows: lista de listas ya ordenadas como columns
    """
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(title, styles["Title"]))
        story.append(Spacer(1, 12))

        data = [columns] + rows
        tbl = Table(data, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f0f0f0")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.HexColor("#333333")),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,0), 10),

            ("GRID", (0,0), (-1,-1), 0.25, colors.HexColor("#aaaaaa")),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#fcfcfc")]),
            ("FONTSIZE", (0,1), (-1,-1), 9),
            ("ALIGN", (0,0), (-1,-1), "LEFT"),
        ]))
        story.append(tbl)

        doc.build(story)
        pdf = buffer.getvalue()
        buffer.close()

        return Response(
            pdf,
            mimetype="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-store",
            },
        )
    except ImportError:
        # reportlab no está instalado
        return err(
            "Exportar a PDF requiere la librería 'reportlab'. Instálala con: pip install reportlab",
            code="PDF_DEPENDENCY_MISSING",
            status=501
        )

# ----------------- Export: Stock por Categoría -----------------
@reports_bp.route("/stock-by-category/export/csv", methods=["GET"])
@token_required
def export_stock_by_category_csv(*args, **kwargs):
    try:
        con = get_db_connection(); cur = con.cursor(dictionary=True)
        rows = _q_stock_by_category(cur)
        cur.close(); con.close()

        header = ["Categoría", "Stock total"]
        keymap = ["category", "total_stock"]
        fname = f"stock_por_categoria_{date.today().isoformat()}.csv"
        return _csv_response(fname, header, rows, keymap)
    except DBError as e:
        return err("No se pudo exportar CSV", details={"db": str(e)})
    except Exception as e:
        return err(str(e))

@reports_bp.route("/stock-by-category/export/pdf", methods=["GET"])
@token_required
def export_stock_by_category_pdf(*args, **kwargs):
    try:
        con = get_db_connection(); cur = con.cursor(dictionary=True)
        rows = _q_stock_by_category(cur)
        cur.close(); con.close()

        columns = ["Categoría", "Stock total"]
        table_rows = [[r.get("category",""), str(r.get("total_stock",0))] for r in rows]
        fname = f"stock_por_categoria_{date.today().isoformat()}.pdf"
        return _pdf_response_simple("Stock por Categoría", columns, table_rows, fname)
    except DBError as e:
        return err("No se pudo exportar PDF", details={"db": str(e)})
    except Exception as e:
        return err(str(e))

# ----------------- Export: Órdenes por Mes -----------------
@reports_bp.route("/orders-history/export/csv", methods=["GET"])
@token_required
def export_orders_history_csv(*args, **kwargs):
    try:
        con = get_db_connection(); cur = con.cursor(dictionary=True)
        rows = _q_orders_history(cur)
        cur.close(); con.close()

        header = ["Mes", "Órdenes"]
        keymap = ["month", "count"]
        fname = f"ordenes_por_mes_{date.today().isoformat()}.csv"
        return _csv_response(fname, header, rows, keymap)
    except DBError as e:
        return err("No se pudo exportar CSV", details={"db": str(e)})
    except Exception as e:
        return err(str(e))

@reports_bp.route("/orders-history/export/pdf", methods=["GET"])
@token_required
def export_orders_history_pdf(*args, **kwargs):
    try:
        con = get_db_connection(); cur = con.cursor(dictionary=True)
        rows = _q_orders_history(cur)
        cur.close(); con.close()

        columns = ["Mes", "Órdenes"]
        table_rows = [[r.get("month",""), str(r.get("count",0))] for r in rows]
        fname = f"ordenes_por_mes_{date.today().isoformat()}.pdf"
        return _pdf_response_simple("Órdenes por Mes", columns, table_rows, fname)
    except DBError as e:
        return err("No se pudo exportar PDF", details={"db": str(e)})
    except Exception as e:
        return err(str(e))
