from flask import Flask
from app.utils.env_loader import load_env

def create_app():
    load_env()

    app = Flask(
        __name__,
        template_folder='templates',  # habilita render_template()
        # static_folder='static'       # por si luego agregas CSS o JS
    )

    from app.routes import purchase_report_bp
    app.register_blueprint(purchase_report_bp)

    return app
