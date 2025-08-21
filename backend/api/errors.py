# api/errors.py
from flask import jsonify

class APIError(Exception):
    status_code = 400
    code = "API_ERROR"

    def __init__(self, message="Error", status_code=None, code=None, details=None):
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code
        self.message = message
        self.details = details or {}

    def to_response(self):
        return jsonify({
            "ok": False,
            "error": self.message,
            "code": self.code,
            "details": self.details,
        }), self.status_code

class ValidationError(APIError):
    status_code = 400
    code = "VALIDATION_ERROR"

class ConflictError(APIError):
    status_code = 409
    code = "CONFLICT"

class NotFoundError(APIError):
    status_code = 404
    code = "NOT_FOUND"

class UnauthorizedError(APIError):
    status_code = 401
    code = "UNAUTHORIZED"

class ForbiddenError(APIError):
    status_code = 403
    code = "FORBIDDEN"

class DatabaseError(APIError):
    status_code = 500
    code = "DB_ERROR"

def register_error_handlers(app):
    # Errores personalizados
    for exc in (APIError, ValidationError, ConflictError, NotFoundError,
                UnauthorizedError, ForbiddenError, DatabaseError):
        app.register_error_handler(exc, lambda e: e.to_response())

    # Errores de JWT: devolver JSON homogéneo
    try:
        from flask_jwt_extended.exceptions import NoAuthorizationError, InvalidHeaderError, JWTExtendedException
        def _jwt_error(e):
            return jsonify({"ok": False, "error": str(e), "code": "AUTH_ERROR"}), 401
        app.register_error_handler(NoAuthorizationError, _jwt_error)
        app.register_error_handler(InvalidHeaderError, _jwt_error)
        app.register_error_handler(JWTExtendedException, _jwt_error)
    except Exception:
        pass

    # 404 homogéneo (si llega a caer acá)
    @app.errorhandler(404)
    def _not_found(_e):
        return jsonify({"ok": False, "code": "NOT_FOUND", "error": "Recurso no encontrado"}), 404

    # 500 genérico para excepciones no controladas
    @app.errorhandler(Exception)
    def _internal_error(e):
        # Evitar doble manejo si ya es APIError
        if isinstance(e, APIError):
            return e.to_response()
        return jsonify({"ok": False, "code": "INTERNAL_ERROR", "error": str(e)}), 500
