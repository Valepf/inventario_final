# api/__init__.py
import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

def create_app():
    load_dotenv()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    templates_path = os.path.join(base_dir, "templates")
    static_path = os.path.join(base_dir, "static")

    app = Flask(
        __name__,
        template_folder=templates_path,
        static_folder=static_path,
        static_url_path="/static",
    )

    # ---- Config ----
    secret = os.getenv("SECRET_KEY", "clave_por_defecto")
    app.config["SECRET_KEY"] = secret
    app.config["JWT_SECRET_KEY"] = secret
    app.config["JWT_TOKEN_LOCATION"] = ["headers"]
    app.config["JWT_HEADER_NAME"] = "Authorization"
    app.config["JWT_HEADER_TYPE"] = "Bearer"
    app.config["JSON_SORT_KEYS"] = False  # Mantener orden del payload

    # Evitar 308 por barras finales
    app.url_map.strict_slashes = False

    # ---- CORS ----
    CORS(
        app,
        resources={
            # Módulos principales (API y vistas servidas por Flask)
            r"/(products|categories|orders|reports|suppliers|users|dashboard|security|static)/*": {
                "origins": [r"http://localhost(:\d+)?", r"http://127\.0\.0\.1(:\d+)?"],
                "supports_credentials": False,
                "allow_headers": ["Content-Type", "Authorization"],
                "expose_headers": ["Content-Type", "Authorization"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            },
            # /auth: login/register/validate (validate usa Authorization)
            r"/auth/*": {
                "origins": [r"http://localhost(:\d+)?", r"http://127\.0\.0\.1(:\d+)?"],
                "supports_credentials": False,
                "allow_headers": ["Content-Type", "Authorization"],
                "methods": ["POST", "GET", "OPTIONS"],
            },
        },
    )

    # ---- JWT ----
    jwt = JWTManager(app)

    @jwt.unauthorized_loader
    def _jwt_unauthorized(err_msg):
        return jsonify({"ok": False, "code": "UNAUTHORIZED", "error": f"Falta el token: {err_msg}"}), 401

    @jwt.invalid_token_loader
    def _jwt_invalid_token(err_msg):
        return jsonify({"ok": False, "code": "INVALID_TOKEN", "error": f"Token inválido: {err_msg}"}), 401

    @jwt.expired_token_loader
    def _jwt_expired_token(jwt_header, jwt_payload):
        return jsonify({"ok": False, "code": "TOKEN_EXPIRED", "error": "El token expiró"}), 401

    @jwt.revoked_token_loader
    def _jwt_revoked_token(jwt_header, jwt_payload):
        return jsonify({"ok": False, "code": "TOKEN_REVOKED", "error": "El token fue revocado"}), 401

    # ---- Blueprints ----
    from api.routes.products import products_bp
    from api.routes.categories import categories_bp
    from api.routes.orders import orders_bp
    from api.routes.reports import reports_bp
    from api.routes.suppliers import suppliers_bp
    from api.routes.users import users_bp
    from api.routes.auth import auth_bp
    from api.routes.dashboard import dashboard_bp
    from api.routes.web import web_bp

    app.register_blueprint(products_bp,   url_prefix="/products")
    app.register_blueprint(categories_bp, url_prefix="/categories")
    app.register_blueprint(orders_bp,     url_prefix="/orders")
    app.register_blueprint(reports_bp,    url_prefix="/reports")
    app.register_blueprint(suppliers_bp,  url_prefix="/suppliers")
    app.register_blueprint(users_bp,      url_prefix="/users")
    app.register_blueprint(auth_bp,       url_prefix="/auth")
    app.register_blueprint(dashboard_bp,  url_prefix="/dashboard")
    
    app.register_blueprint(web_bp)  # sin prefijo (sirve HTML)

    # ---- Health check (opcional) ----
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"ok": True, "service": "api", "path": "/health"})

    # ⬇️ Registrá manejadores centrales (api/errors.py)
    from api.errors import register_error_handlers
    register_error_handlers(app)

    # ---- Normalización de OPTIONS (CORS preflight) ----
    @app.before_request
    def _handle_options_preflight():
        if request.method == "OPTIONS":
            return ("", 204)

    # ---- Favicon opcional (limpia 404 en logs) ----
    @app.route("/favicon.ico")
    def favicon():
        fav_path = os.path.join(app.static_folder, "favicon.ico")
        if os.path.exists(fav_path):
            return send_from_directory(app.static_folder, "favicon.ico")
        return ("", 204)

    return app
