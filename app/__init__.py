from flask import Flask

from app.errors import error
from .config import Config, TestConfig
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'loggedout.login'
csrf = CSRFProtect()

def create_app(config_class):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config_class)
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)

    from app.errors import error as errors_bp
    app.register_blueprint(errors_bp)
    from app.routes import bp_register
    bp_register(app)

    if config_class == TestConfig:
        from app.testing import testing 
        app.register_blueprint(testing)

    return app

from app import models