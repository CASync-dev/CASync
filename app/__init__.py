from flask import Flask
from .config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config.from_object(Config)
db = SQLAlchemy(app=app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

from app import models, error, routes