from .loggedin.loggedin import loggedin
from .loggedout.loggedout import loggedout
from .api import api_cal, api_events, api_users, api_groups, api_friends

# Registers the blueprints for routes.
def bp_register(app):
    app.register_blueprint(loggedin)
    app.register_blueprint(loggedout)
    app.register_blueprint(api_cal.api_cal)
    app.register_blueprint(api_events.api_events)
    app.register_blueprint(api_users.api_users)
    app.register_blueprint(api_friends.api_friends)
    app.register_blueprint(api_groups.api_groups)