import unittest

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_migrate import Migrate, upgrade
from extensions import db
from models import Calendar, User, Event
from services.ical import import_ical
from config import config

# This is the Factory function to create the Flask app with the appropriate configuration
# Config can be set via the FLASK_CONFIG environment variable (e.g. "development", "production", "testing")
# Configs are defined in config.py and include database settings, secret keys, etc.
def create_app(config_name='default'):
    # -- Initialize the Flask app and load the configuration
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    #Initialize the database and migration extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    # Run database migrations on startup (skipped in testing: setUp uses db.create_all() instead)
    if not app.config.get('TESTING'):
        with app.app_context():
            upgrade()

    # --- Session login logic | will be replaced with real auth later
    # for now we just use a simple session flag to simulate login/logout
    @app.context_processor
    # This makes the logged_in variable available in all templates 
    # so we can show/hide things based on login status
    def inject_auth():
        return {'logged_in': session.get('logged_in', False)}

    # A simple decorator to protect routes that require login
    # If the user is not logged in, they will be redirected to the home page.
    # In a real app, we would redirect to a login page instead and show a message.
    def require_login():
        if not session.get('logged_in'):
            return redirect(url_for('home'))
        return None

    # --- Page routes
    @app.route("/")
    def index():
        return render_template("homepage.html")

    @app.route("/dash")
    def dash():
        guard = require_login()
        if guard:
            return guard
        return render_template("dash.html")

    @app.route("/schedule")
    def schedule():
        guard = require_login()
        if guard:
            return guard
        return render_template("schedule.html")

    @app.route("/groups")
    def groups():
        guard = require_login()
        if guard:
            return guard
        return render_template("groups.html")

    @app.route("/friends")
    def friends():
        guard = require_login()
        if guard:
            return guard
        return render_template("friends.html")

    @app.route("/settings")
    def settings():
        guard = require_login()
        if guard:
            return guard
        return render_template("settings.html")

    @app.route("/login")
    def login():
        return render_template("login.html")

    @app.route("/register")
    def register():
        return render_template("register.html")

    @app.route("/home")
    def home():
        return render_template("homepage.html")

    @app.route("/faq")
    def faq():
        return render_template("faq.html")

    # --- API routes
    @app.route("/dev/login")
    # This is a simple route to simulate logging in for development purposes
    # It sets a session flag to indicate the user is logged in.
    def dev_login():
        session['logged_in'] = True
        return redirect(url_for('dash'))

    # This is a simple route to simulate logging out for development purposes
    # It sets a session flag to indicate the user is logged out.
    @app.route("/dev/logout")
    def dev_logout():
        session['logged_in'] = False
        return redirect(url_for('home'))

    # These API routes are for testing 
    # They allow us to fetch data from 
    # the database and test the iCal import functionality.
    @app.route("/api/events")
    def api_events():
        events = Event.query.all()
        return jsonify([e.to_dict() for e in events])

    @app.route("/api/user")
    def api_user():
        user = User.query.first()
        if not user:
            return jsonify({}), 404
        return jsonify({'id': user.id, 'username': user.username, 'email': user.email})

    @app.route("/api/calendars")
    def api_calendars():
        calendars = Calendar.query.all()
        return jsonify([c.to_dict() for c in calendars])

    # This API route allows the frontend to send an iCal feed URL to be imported.
    # It calls the import_ical function from services/ical.p
    # which handles validation, fetching, and parsing of the iCal data.
    @app.route("/api/import-ical", methods=["POST"])
    def api_import_ical():
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Request body must be JSON."}), 400
        result, error = import_ical(data.get("url"))
        if error:
            return jsonify({"error": error}), 400
        return jsonify(result), 200

    # Error handling
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    return app

# Run the app
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=8080)
