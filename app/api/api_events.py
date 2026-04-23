from datetime import datetime
from app import db
from flask import Blueprint, jsonify, request
from app.models import Calendar, User, Event
from flask_login import current_user, login_required


api_events = Blueprint('api_events', __name__)

# -- API EVENT ROUTES

# API route to get all events for a user - this is used by the schedule page to load the events onto the calendar
# it accpets the user id as a parameter and returns a list of events for that user in json format
# not sure if asking for the user id in the url is the best way to do this
# but it works for now, we can change it later if we want to use a different auth system or something

# Upd: Changed def name (Couldn't think of a better name for the blueprint)
@api_events.route("/api/events/")
@login_required
def api_eventslist():
    # Assuming the user is authenticated and we can get their ID from the session
    user_id = current_user.id
    events = Event.query.where(Event.user_id == user_id).all()
    return jsonify([e.to_dict() for e in events])

# create event API route - accepts a POST request with the event details in the body and creates a new event for the user
@api_events.route("/api/events", methods=["POST"])
@login_required
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
@api_events.route("/api/events/<int:event_id>", methods=["DELETE"])
@login_required
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
@api_events.route("/api/events/<int:event_id>", methods=["PUT"])
@login_required
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
