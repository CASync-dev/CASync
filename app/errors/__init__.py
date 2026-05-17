from flask import Blueprint

error = Blueprint('errors', __name__, template_folder='../templates/errors')

from app.errors import handlers