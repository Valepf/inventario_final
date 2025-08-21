# main.py
from api import create_app
import os

app = create_app()

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "true").lower() == "true"

    print(f"Iniciando el sistema de gestión en http://{host}:{port}...")
    # Si querés evitar doble arranque/log en modo debug:
    # app.run(debug=debug, host=host, port=port, use_reloader=False)
    app.run(debug=debug, host=host, port=port)
