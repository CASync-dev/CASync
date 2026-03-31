from flask import Flask, render_template, jsonify, request
from flask_migrate import Migrate, upgrade
from extensions import db
from models import Calendar, User, Event
from services.ical import import_ical

app = Flask(__name__)
# Configure the database URI and initialize the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db.init_app(app)
migrate = Migrate(app, db)
# Run the initial migration to create the database schema
with app.app_context():
    upgrade()


# Page routes
@app.route("/")
def index():
    return render_template("dash.html")

@app.route("/dash")
def dash():
    return render_template("dash.html")

@app.route("/schedule")
def schedule():
    return render_template("schedule.html")


@app.route("/groups")
def groups():
    return render_template("groups.html")


@app.route("/friends")
def friends():
    return render_template("friends.html")


@app.route("/settings")
def settings():
    return render_template("settings.html")

# API routes - at the moment they retrun json responses but thats not long term
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



# Error handling
@app.errorhandler(404)
def page_not_found(e):
    return render_template("errors/404.html"), 404



if __name__ == "__main__":
    app.run(debug=True, port=8080)
