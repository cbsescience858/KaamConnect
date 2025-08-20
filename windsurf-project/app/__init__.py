from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_migrate import Migrate
from config import Config
from flask import session
from flask_login import current_user
from app.services.translation import translation_service
from app.lib.targetcursor import render_attrs as targetcursor

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO()

def create_app(config_class=Config):
    """Creates and configures the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions here
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Set the login view
    
    from app.models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    socketio.init_app(app, cors_allowed_origins="*")

    # Expose a translation helper to all templates
    @app.context_processor
    def inject_translation_helper():
        try:
            lang = current_user.preferred_language if getattr(current_user, 'is_authenticated', False) and current_user.is_authenticated else session.get('preferred_language', 'en')
        except Exception:
            lang = 'en'

        def t(key, **kwargs):
            return translation_service.translate_key(key, lang, **kwargs)

        return dict(t=t, current_lang=lang, targetcursor=targetcursor)

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.jobs import jobs_bp
    from .routes.chat import chat_bp
    from .routes.payments import payments_bp
    from .routes.language import language_bp
    from .routes.skills import skills_bp
    from .routes.location import location_bp
    from .routes.main import main as main_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(jobs_bp, url_prefix='/jobs')
    app.register_blueprint(payments_bp, url_prefix='/payments')
    app.register_blueprint(language_bp, url_prefix='/language')
    app.register_blueprint(skills_bp, url_prefix='/skills')
    app.register_blueprint(location_bp, url_prefix='/location')
    # Chat blueprint is for SocketIO events, no prefix needed
    app.register_blueprint(chat_bp)
    app.register_blueprint(main_bp)

    with app.app_context():
        from . import models  # Import models

    return app
