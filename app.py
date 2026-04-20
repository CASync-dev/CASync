import os
from datetime import datetime

from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from extensions import db
from models import Calendar, User, Event
from services.ical import import_ical
from form import EventForm, IcalImportForm


app = Flask(__name__)
# Secret key for session logic
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')  # swap for real env var later
# Configure the database URI and initialize the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db.init_app(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)


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


@app.route("/settings", methods=['GET', 'POST'])
def settings():
    # login protection
    guard = require_login()
    if guard: return guard
    # ical submit form
    form = IcalImportForm()
    if form.validate_on_submit():
        url = form.ical_url.data
        user_id = int(form.user_id.data)
        # Process the iCal import logic here
        result, error = import_ical(url, user_id)
        if error:
            flash(f"Error importing iCal: {error}", "error")
        else:
            imported = result.get('imported') or result.get('created', 0)
            updated = result.get('updated', 0)
            flash(f"Imported {imported} events, updated {updated}.", "success")

    return render_template("settings.html", form=form)

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

# -- API EVENT ROUTES

# API route to get all events for a user - this is used by the schedule page to load the events onto the calendar
# it accpets the user id as a parameter and returns a list of events for that user in json format
# not sure if asking for the user id in the url is the best way to do this
# but it works for now, we can change it later if we want to use a different auth system or something
@app.route("/api/events/<int:user_id>")
def api_events(user_id):
    events = Event.query.where(Event.user_id == user_id).all()
    return jsonify([e.to_dict() for e in events])

# create event API route - accepts a POST request with the event details in the body and creates a new event for the user
@app.route("/api/events", methods=["POST"])
def api_create_event():
    """
        Expects a JSON body like this:
    {
        "title": "Event Title",
        "description": "Event Description",
        "date": "2024-07-01",
        "start_time": "14:00",
        "end_time": "15:00",
        "user_id": 1
        "location": "Event Location",
        "color": "indigo"  
    }
    """
    data = request.get_json()
    # We should add some validation here to make sure the data is in the right format and all required fields are present, but for now we'll just assume it's correct
    event = Event(
        title=data['title'],
        description=data.get('description', ''),
        date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
        start_time=datetime.strptime(data['start_time'], '%H:%M').time(),
        end_time=datetime.strptime(data['end_time'], '%H:%M').time(),
        location=data.get('location'),
        color=data.get('color', 'indigo'),
        user_id=data['user_id']
    )
    db.session.add(event)
    db.session.commit()
    return jsonify(event.to_dict()), 201

# API route to delete an event - accepts a DELETE request with the event id in the url and deletes the event from the database
@app.route("/api/events/<int:event_id>", methods=["DELETE"])
def api_delete_event(event_id):
    event = Event.query.get(event_id)
    # check event belongs to user - we should get the user id from the session or something instead of passing it in the url, but for now we'll just assume it's correct
    # check if it exists
    if not event:
        return jsonify({"error": "Event not found"}), 404
    # check if event is custom (not imported from ical) - we don't want to allow deletion of imported events through this route
    if event.ical_id:
        return jsonify({"error": "Cannot delete imported events"}), 400
    db.session.delete(event)
    db.session.commit()
    return jsonify({"message": "Event deleted"}), 200

# API route to edit an event - accepts a PUT request with the event id in the url and the updated event details in the body, and updates the event in the database
@app.route("/api/events/<int:event_id>", methods=["PUT"])
def api_edit_event(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    # check if event is custom (not imported from ical) - we don't want to allow editing of imported events through this route
    if event.ical_id:
        return jsonify({"error": "Cannot edit imported events"}), 400
    data = request.get_json()
    # update the event details - again we should add some validation here but we'll assume the data is correct for now
    event.title = data['title']
    event.description = data.get('description', '')
    event.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    event.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
    event.end_time = datetime.strptime(data['end_time'], '%H:%M').time()
    event.location = data.get('location')
    event.color = data.get('color', 'indigo')
    db.session.commit()
    return jsonify(event.to_dict()), 200


# -- API CALENDAR ROUTES
@app.route("/api/calendars/<int:user_id>")
def api_calendars(user_id):
    calendars = Calendar.query.where(Calendar.user_id == user_id).all()
    return jsonify([{"id": c.id, "ical_url": c.ical_url, "synced_at": c.synced_at.isoformat()} for c in calendars])

@app.route("/api/import-ical/<int:user_id>", methods=["POST"])
def api_import_ical(user_id):
    """
    POST /api/import-ical/<user_id>
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
    result, error = import_ical(data.get('url'), user_id)

    if error:
        # If there was an error during import, return it with a 400 status code
        return jsonify({"error": error}), 400

    # On success, return the result (e.g. number of events imported) with a 200 status code
    return jsonify(result), 200

@app.route("/api/sync-cal/<int:user_id>", methods=["POST"])
def api_sync_cal(user_id):
    """
    POST /api/sync-cal/<user_id>

    Gets all calendars for the user, then for each calendar fetches the latest events from the iCal 
    feed and updates the database accordingly. This allows us to keep imported events up to date 
    with any changes in the original calendar.
    """
    calendars = Calendar.query.where(Calendar.user_id == user_id).all()
    total_created = 0
    total_updated = 0
    errors = []
    for cal in calendars:
        result, error = import_ical(cal.ical_url, user_id)
        if error:
            errors.append({"calendar_id": cal.id, "error": error})
        else:
            total_created += result.get("created", 0)
            total_updated += result.get("updated", 0)
    if errors and not (total_created or total_updated):
        return jsonify({"error": errors[0]["error"]}), 400
    return jsonify({"created": total_created, "updated": total_updated}), 200

# -- OTHER API ROUTES

@app.route("/api/user")
def api_user():
    user = User.query.first()
    if not user:
        return jsonify({}), 404
    return jsonify({'id': user.id, 'username': user.username, 'email': user.email})

# This is just a test route to get a list of users
@app.route("/api/users", methods=["get"])
def api_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])

# -- Error handling
@app.errorhandler(404)
def page_not_found(e):
    return render_template("errors/404.html"), 404



if __name__ == "__main__":
    app.run(debug=True, port=8080)
