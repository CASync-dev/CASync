from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import os
from flask import Flask, render_template, jsonify, session, redirect, url_for
from extensions import db
from models import Calendar, User, Event
from services.ical import import_ical

app = Flask(__name__)
# Secret key for session logic
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')  # swap for real env var later
# Configure the database URI and initialize the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db.init_app(app)

# --- Session login logic
@app.context_processor
# This function injects the 'logged_in' variable into all tempaltes
def inject_auth():
    return {'logged_in': session.get('logged_in', False)}
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
    if guard: return guard
    return render_template("dash.html")

@app.route("/schedule")
def schedule():
    guard = require_login()
    if guard: return guard
    return render_template("schedule.html")


@app.route("/groups")
def groups():
    guard = require_login()
    if guard: return guard
    return render_template("groups.html")


@app.route("/friends")
def friends():
    guard = require_login()
    if guard: return guard
    return render_template("friends.html")


@app.route("/settings")
def settings():
    guard = require_login()
    if guard: return guard
    return render_template("settings.html")

# Login, register, homepage and faq currently have a different style from the other webpages.
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


#--- API routes - at the moment they return json responses but thats not long term

#curent mock login logic - just toggles login state for testing purposes
# the login and logout pages currently just toggle the session variable 
# and redirect to the appropriate page, but this will be replaced with 
# real login logic later on
@app.route("/dev/login")
def dev_login():
    session['logged_in'] = True
    return redirect(url_for('dash'))

@app.route("/dev/logout")
def dev_logout():
    session.clear()
    return redirect(url_for('home'))

# API route to get all events for a user - this is used by the schedule page to load the events onto the calendar
# it accpets the user id as a parameter and returns a list of events for that user in json format
# not sure if asking for the user id in the url is the best way to do this
# but it works for now, we can change it later if we want to use a different auth system or something
@app.route("/api/events/<int:user_id>")
def api_events(user_id):
    events = Event.query.where(Event.user_id == user_id).all()
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

@app.route("/api/import-ical", methods=["POST"])
def api_import_ical():
    """
    POST /api/import-ical
    Body: { "url": "<ical feed url>" }

    Passes the URL and user to services/ical.py which validates, fetches,
    parses, and saves the events. Returns 200 on success or 400 on failure.
    """
    # Get JSON data from the request body
    data = request.get_json(silent=True)

    if not data:
        # If the body isn't valid JSON, get_json returns None. silent=True prevents it from raising an error.
        return jsonify({"error": "Request body must be JSON."}), 400

    # Call the main import function in services/ical.py, which returns (result, error)
    result, error = import_ical(data.get("url"))

    if error:
        # If there was an error during import, return it with a 400 status code
        return jsonify({"error": error}), 400

    # On success, return the result (e.g. number of events imported) with a 200 status code
    return jsonify(result), 200


# This is just a test route to get a list of users
@app.route("/api/users", methods=["get"])
def api_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])


# Error handling
@app.errorhandler(404)
def page_not_found(e):
    return render_template("errors/404.html"), 404



if __name__ == "__main__":
    app.run(debug=True, port=8080)
