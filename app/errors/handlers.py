from flask import render_template
from app.errors import error

@error.app_errorhandler(404)
def page_not_found(e):
    return render_template("errors/404.html"), 404

# Raised by the rate limiter (see app/__init__.py) when an IP burns through its
# budget on login, register, forgot-password or resend-confirmation.
@error.app_errorhandler(429)
def too_many_requests(e):
    return render_template("errors/429.html"), 429

