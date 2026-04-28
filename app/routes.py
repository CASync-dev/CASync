from app import app
from .loggedin.loggedin import loggedin
from .loggedout.loggedout import loggedout
from .api import api_cal, api_events, api_users

# Registers the blueprints for routes.
app.register_blueprint(loggedin)
app.register_blueprint(loggedout)
app.register_blueprint(api_cal.api_cal)
app.register_blueprint(api_events.api_events)
app.register_blueprint(api_users.api_users)
