# api/routes/web.py
from flask import Blueprint, render_template, redirect, url_for

web_bp = Blueprint("web", __name__)

@web_bp.route("/")
def root():
    # Al abrir http://127.0.0.1:5000/ te manda al login
    return redirect(url_for("web.login"))

# ---------- LOGIN ----------
@web_bp.route("/login", endpoint="login")
def login_page():
    return render_template("login.html")

@web_bp.route("/security/login")
def login_alias():
    return redirect(url_for("web.login"))

# ---------- PÁGINAS ----------
@web_bp.route("/dashboard", endpoint="dashboard")
def dashboard_page():
    return render_template("dashboard.html")

@web_bp.route("/categorias", endpoint="categorias")
def categories_page():
    return render_template("categories.html")

@web_bp.route("/productos", endpoint="productos")
def products_page():
    return render_template("products.html")

@web_bp.route("/proveedores", endpoint="proveedores")
def suppliers_page():
    return render_template("suppliers.html")

@web_bp.route("/ordenes", endpoint="ordenes")
def orders_page():
    return render_template("orders.html")

@web_bp.route("/reportes", endpoint="reportes")
def reports_page():
    return render_template("reports.html")

@web_bp.route("/usuarios", endpoint="usuarios")
def users_page():
    return render_template("users.html")
