from flask import Flask

from app.errors import error
from .config import Config, TestConfig
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'loggedout.login'
csrf = CSRFProtect()

# Rate limiting for the endpoints that either send email or guess passwords.
# There are no default limits — only the routes that opt in with @limiter.limit
# are throttled, so ordinary page loads and the dashboard's API polling are
# untouched. get_remote_address reads REMOTE_ADDR, which ProxyFix has already
# rewritten to the real client IP (see wsgi.py).
#
# Storage is in-process: each gunicorn worker keeps its own counters, so the
# effective limit is roughly (limit x workers). That's fine for deterring abuse
# and avoids standing up Redis just for this; point RATELIMIT_STORAGE_URI at a
# shared store if exact limits ever matter.
limiter = Limiter(key_func=get_remote_address)

def create_app(config_class):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config_class)
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)

    from app.errors import error as errors_bp
    app.register_blueprint(errors_bp)
    from app.routes import bp_register
    bp_register(app)

    return app

from app import models