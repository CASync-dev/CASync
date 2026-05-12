from datetime import datetime
from app import db
from flask import Blueprint, jsonify, request
from app.models import Calendar, User, Event
from flask_login import current_user, login_required

api_events = Blueprint('api_events', __name__)

# -- API EVENT ROUTES
"""
   Standard Get Events Response:
   - Routes should reposnd in json with a list of user ids, each user has a list of events wich have their respective details
   - This sets an easily decodable format.
    {
    "1": {
    "events": {
        "1": {
        "title": "Agile Web Development, Lab-03",
        "description": "CITS3403_SEM-1_CR, Lab-03, 04\nAgile Web Development\nStaff: -\nLocation: HACKH: [  G09] Fay Gale Studio",
        "date": "2026-04-23",
        "startTime": "12:00",
        "endTime": "14:00",
        "user_id": 1,
        "location": "HACKH: [  G09] Fay Gale Studio",
        "color": null,
        "ical_id": 1,
        "ical_uid": "uid28",
        "id": 29
        },
        "2": {
        "title": "Agile Web Development, Lecture-05",
        "description": "CITS3403_SEM-1_CR, Lecture-05\nAgile Web Development\nStaff: Dr. Smith\nLocation: ENGL: [  G12] Lecture Theatre",
        "date": "2026-04-25",
        "startTime": "10:00",
        "endTime": "12:00",
        "user_id": 1,
        "location": "ENGL: [  G12] Lecture Theatre",
        "color": "indigo",
        "ical_id": 1,
        "ical_uid": "uid31",
        "id": 32
        }
    }
    },
    "2": {
    "events": {
        "1": {
        "title": "CITS2002 Systems Programming, Lab-04",
        "description": "CITS2002_SEM-1_CR, Lab-04\nSystems Programming\nStaff: -\nLocation: CSSE: [  G15] Computer Lab",
        "date": "2026-04-24",
        "startTime": "13:00",
        "endTime": "15:00",
        "user_id": 2,
        "location": "CSSE: [  G15] Computer Lab",
        "color": "emerald",
        "ical_id": 2,
        "ical_uid": "uid45",
        "id": 46
        }
    }
    }
    }
"""

# API route to get all events for a user - this is used by the schedule page to load the events onto the calendar
#mostly a dev route
@api_events.route("/api/events/")
@login_required
def api_eventslist():
    # test route the returns all events from all users in the standard psciefied above
    events = Event.query.all()
    users = User.query.all()
    user_dict = {user.id: {"events": {}} for user in users}
    for event in events:
        user_dict[event.user_id]["events"][str(event.id)] = event.to_dict()
    return jsonify(user_dict)

# Api route that accpets a start and and range of days and returns all events for the user in that date range 
# acceepts a format like this: GET /api/events/me?start=2026-04-21&end=2026-04-25
# responds with a list of events in that date range for the current user
@api_events.route("/api/events/me")
def api_events_range():
    """
    Accepts a start and end date as query parameters as:
    GET /api/events/me?start=2026-04-21&end=2026-04-25  
    Returns all events for the current user in the specified date range, used for loading events onto the calendar in a single request'
    response has the format:
    {
        "1": {
            "events": {
                "1": {
                    "title": "Event Title",
                    "description": "Event Description",
                    "date": "2024-07-01",
                    "startTime": "14:00",
                    "endTime": "15:00",
                    "user_id": 1,
                    "username": "exampleuser",
                    "location": "Event Location",
                    "color": "indigo",
                    "ical_id": null,
                    "ical_uid": null,
                    "id": 1
                },
                ...

    """

    start_str = request.args.get('start')
    end_str = request.args.get('end')
    if not start_str or not end_str:
        return jsonify({"error": "Missing start or end date"}), 400
    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format, should be YYYY-MM-DD"}), 400
    events = Event.query.where(
        Event.user_id == current_user.id,
        Event.date >= start_date,
        Event.date <= end_date
    ).all()
    user_id = str(current_user.id)
    indexed_events = {str(i + 1): e.to_dict() for i, e in enumerate(events)}
    return jsonify({user_id: {"events": indexed_events}})

# API route to retrieve a specific Users events - accepts a user id as a url parameter and returns all events for that user
# Mostly same as above but checks if the current logged in user is friends with the user id provided and only returns events if they are friends, otherwise returns an error message
@api_events.route("/api/events/<int:user_id>")
@login_required
def api_user_events(user_id):
    """
    Accepts a start and end date as query parameters as:
    GET /api/events/<int:user-id>?start=2026-04-21&end=2026-04-25  
    Returns all events for the current user in the specified date range, used for loading events onto the calendar in a single request'
    response has the format:
    {
        "1": {
            "events": {
                "1": {
                    "title": "Event Title",
                    "description": "Event Description",
                    "date": "2024-07-01",
                    "startTime": "14:00",
                    "endTime": "15:00",
                    "user_id": 1,
                    "username": "exampleuser",
                    "location": "Event Location",
                    "color": "indigo",
                    "ical_id": null,
                    "ical_uid": null,
                    "id": 1
                },
                ...

    """

    start_str = request.args.get('start')
    end_str = request.args.get('end')
    if not start_str or not end_str:
        return jsonify({"error": "Missing start or end date"}), 400
    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format, should be YYYY-MM-DD"}), 400
    # check if the user is friends with the user id provided, if not return an error message
    # TODO: there is no friends system yet but we will do that chekck here

    events = Event.query.where(
        Event.user_id == user_id,
        Event.date >= start_date,
        Event.date <= end_date
    ).all()
    user_id = str(current_user.id)
    indexed_events = {str(i + 1): e.to_dict() for i, e in enumerate(events)}
    return jsonify({user_id: {"events": indexed_events}})

@api_events.route("/api/events/group/<int:group_id>", methods=["POST"])
@login_required
def api_group_events(group_id):
    # This route gets all the events for a group of users in the groups table. Also accepts a start and end date as query parameters to limit the events returned to a specific date range, same format as above routes
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    if not start_str or not end_str:
        return jsonify({"error": "Missing start or end date"}), 400
    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format, should be YYYY-MM-DD"}), 400
    # check if the user is in the group provided, if not return an error message
    

# -- Manipulation routes (create, edit, delete) --

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
        user_id=current_user.id

    )
    db.session.add(event)
    db.session.commit()
    return jsonify(event.to_dict()), 201

# API route to delete an event - accepts a DELETE request with the event id in the url and deletes the event from the database
@api_events.route("/api/events/<int:event_id>", methods=["DELETE"])
@login_required
def api_delete_event(event_id):
    # check if event exists and belongs to the user
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    if event.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    # check if event is custom (not imported from ical) - we don't want to allow deletion of imported events through this route
    if event.ical_id:
        return jsonify({"error": "Cannot delete imported events"}), 400
    db.session.delete(event)
    db.session.commit()
    return jsonify({"message": "Event deleted"}), 200

# API route to edit an event - accepts a PUT request with the event id in the url and the updated event details in the body, and updates the event in the database
@api_events.route("/api/events/<int:event_id>", methods=["PUT", "GET"])
@login_required
def api_edit_event(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    if event.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
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

@api_events.route("/api/events/<int:event_id>/toggle_going", methods=["POST"])
@login_required
def api_toggle_going(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    if event.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    # toggle the going status
    event.going = not event.going
    db.session.commit()
    return jsonify({"id": event.id, "user_id": event.user_id, "going": event.going}), 200