from flask import Blueprint

testing = Blueprint('testing', __name__)

from app.testing import testing