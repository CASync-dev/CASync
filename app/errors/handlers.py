from flask import render_template
from app.errors import error

@error.app_errorhandler(404)
def page_not_found(e):
    return render_template("errors/404.html"), 404

