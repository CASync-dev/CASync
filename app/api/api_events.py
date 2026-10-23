from datetime import datetime, time, timedelta, timezone
from app import db
from flask import Blueprint, jsonify, request
from app.models import Calendar, GroupEvent, User, Event, Group
from flask_login import current_user, login_required

api_events = Blueprint('api_events', __name__)

VALID_COLORS = {'indigo', 'blue', 'green', 'rose', 'amber', 'orange', 'red', 'purple', 'gray', 'yellow', 'emerald'}

def _validate_event_data(data):
    errors = []
    title = (data.get('title') or '').strip()
    if not title or not data.get('start_time') or not data.get('end_time'):
        errors.append("Please fill in all required fields.")
    if len(data.get('title', '')) > 200:
        errors.append("Title must be 200 characters or fewer.")
    if data.get('start_time') and data.get('end_time'):
        try:
            start = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
            if end <= start:
                errors.append("End time must be after start time.")
        except ValueError:
            errors.append("Invalid datetime format, expected ISO 8601.")
    color = data.get('color')
    if color and color not in VALID_COLORS:
        errors.append(f"Invalid color. Must be one of: {', '.join(sorted(VALID_COLORS))}.")
    if data.get('description') and len(data['description']) > 500:
        errors.append("Description must be 500 characters or fewer.")
    if data.get('location') and len(data['location']) > 300:
        errors.append("Location must be 300 characters or fewer.")
    return errors

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
@login_required
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
    # Match any event that overlaps the [start_date 00:00 UTC, end_date+1 00:00 UTC) window.
    start_dt = datetime.combine(start_date, time(0, 0), tzinfo=timezone.utc)
    end_dt = datetime.combine(end_date, time(0, 0), tzinfo=timezone.utc) + timedelta(days=1)
    events = Event.query.where(
        Event.user_id == current_user.id,
        Event.start_time < end_dt,
        Event.end_time > start_dt
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
    friends = current_user.get_friends()
    if user_id not in [friend.id for friend in friends]:
        return jsonify({"error": "Unauthorized"}), 403

    start_dt = datetime.combine(start_date, time(0, 0), tzinfo=timezone.utc)
    end_dt = datetime.combine(end_date, time(0, 0), tzinfo=timezone.utc) + timedelta(days=1)
    events = Event.query.where(
        Event.user_id == user_id,
        Event.start_time < end_dt,
        Event.end_time > start_dt
    ).all()
    user_id = str(current_user.id)
    indexed_events = {str(i + 1): e.to_dict() for i, e in enumerate(events)}
    return jsonify({user_id: {"events": indexed_events}})

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
        "start_time": "2024-07-01T14:00:00.000Z",
        "end_time": "2024-07-01T15:00:00.000Z",
        "user_id": 1
        "location": "Event Location",
        "color": "indigo"
    }
    start_time and end_time are full ISO datetimes with a timezone offset.
    """
    data = request.get_json()

    # VALIDATE input fields
    errors = _validate_event_data(data)
    if errors:
        return jsonify({"error": "; ".join(errors)}), 400

     # Required fields
    if not data.get('title') or not data.get('start_time') or not data.get('end_time'):
        return jsonify({"error": "Please fill in all required fields."}), 400
    
    # End time after start time
    start = datetime.strptime(data['start_time'], '%Y-%m-%dT%H:%M:%S.%fZ').time()
    end = datetime.strptime(data['end_time'], '%Y-%m-%dT%H:%M:%S.%fZ').time()
    if end <= start:
        return jsonify({"error": "End time must be after start time."}), 400
    

    event = Event(
        title=data['title'],
        description=data.get('description', ''),
        start_time=datetime.fromisoformat(data['start_time'].replace('Z', '+00:00')),
        end_time=datetime.fromisoformat(data['end_time'].replace('Z', '+00:00')),
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
    event = db.session.get(Event, event_id)
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
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    if event.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    # check if event is custom (not imported from ical) - we don't want to allow editing of imported events through this route
    if event.ical_id:
        return jsonify({"error": "Cannot edit imported events"}), 400
    
    data = request.get_json()

    # VALIDATE input fields
    errors = _validate_event_data(data)
    if errors:
        return jsonify({"error": "; ".join(errors)}), 400

    
    
    # VALIDATE input fields
    # Required fields
    if not data.get('title') or not data.get('start_time') or not data.get('end_time'):
        return jsonify({"error": "Please fill in all required fields."}), 400
    
    # End time after start time
    start = datetime.strptime(data['start_time'], '%Y-%m-%dT%H:%M:%S.%fZ').time()
    end = datetime.strptime(data['end_time'], '%Y-%m-%dT%H:%M:%S.%fZ').time()
    if end <= start:
        return jsonify({"error": "End time must be after start time."}), 400
    
    
    # update the event details - again we should add some validation here but we'll assume the data is correct for now
    event.title = data['title']
    event.description = data.get('description', '')
    event.start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
    event.end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
    event.location = data.get('location')
    event.color = data.get('color') or 'indigo'
    db.session.commit()
    return jsonify(event.to_dict()), 200

@api_events.route("/api/events/<int:event_id>/toggle_going", methods=["POST"])
@login_required
def api_toggle_going(event_id):
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    if event.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    # toggle the going status
    event.going = not event.going
    db.session.commit()
    return jsonify({"id": event.id, "user_id": event.user_id, "going": event.going}), 200

@api_events.route("/api/events/group/<int:group_id>", methods=["GET"])
@login_required
def api_group_events(group_id):
    # This route gets all the events for a group of users in the groups table. Also accepts a start and end date as query parameters to limit the events returned to a specific date range, same format as above routes
    # Unlike the above route this one includes the pfp and username of the user in the response as well, to make it easier for the frontend to display the events on the calendar with the correct user information without needing to make additional requests to get the user info
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    if not start_str or not end_str:
        return jsonify({"error": "Missing start or end date"}), 400
    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format, should be YYYY-MM-DD"}), 400
    # check if the user is in the group provided, if not return an error messag
    group = Group.query.get(group_id)
    if not group:
        return jsonify({"error": "Group not found"}), 404
    if not group.is_member():
        return jsonify({"error": "Unauthorized"}), 403
    # get all the user ids in the group and return all events for those users in the specified date range
    user_ids = [user.id for user in group.members]
    events = Event.query.where(
        Event.user_id.in_(user_ids),
        Event.start_time >= start_date,
        Event.end_time <= end_date
    ).all()
    # format the events in the standard format specified above
    # A user
    user_dict = {str(user.id): {"username": user.username, "pfp": user.avatar(200), "events": {}} for user in group.members}
    for event in events:
        user_dict[str(event.user_id)]["events"][str(event.id)] = event.to_dict()

    # Group Events
    g_events = GroupEvent.query.where(
        GroupEvent.group_id == group_id,
        GroupEvent.start_time >= start_date,
        GroupEvent.end_time <= end_date
    ).all()

    group_events = dict()
    glist = []
    for gevent in g_events:
        glist.append(gevent.to_dict())
    
    return jsonify(user_dict)

# Group Event Manipulation (create, edit, delete)

# Group event creation
# Using a similar format to normal events for uniformity
@api_events.route("/api/events/group_events/create/<int:group_id>", methods = ["POST"])
@login_required
def api_create_group_event(group_id):
    if not group_id:
        return jsonify({"Error": "No group provided for group event creation."})
    group = db.session.get(Group, group_id)
    if not group:
        return jsonify({"Error": "Invalid group provided"})
    # Prevent creating group events for groups you're not a member of
    if not group.is_member():
        return jsonify({"Error": "You're not apart of this group!"})
    # Gets form data
    data = request.get_json()
    '''
    Expected format:
    {
        "title": "Event Title",
        "description": "Event Description",
        "start_time": "2024-07-01T14:00:00.000Z",
        "end_time": "2024-07-01T15:00:00.000Z",
        "group_id": 1
        "location": "Event Location",
        "color": "indigo"
    }
    start_time and end_time are full ISO datetimes with a timezone offset.
    ...like normal event creation form, only for group events :)
    '''

    # From normal event creation
    # VALIDATE input fields
    errors = _validate_event_data(data)
    if errors:
        return jsonify({"error": "; ".join(errors)}), 400

     # Required fields
    if not data.get('title') or not data.get('start_time') or not data.get('end_time'):
        return jsonify({"error": "Please fill in all required fields."}), 400
    
    # End time after start time
    start = datetime.strptime(data['start_time'], '%Y-%m-%dT%H:%M:%S.%fZ').time()
    end = datetime.strptime(data['end_time'], '%Y-%m-%dT%H:%M:%S.%fZ').time()
    if end <= start:
        return jsonify({"error": "End time must be after start time."}), 400
    
    g_event = GroupEvent(
        group_id=group_id,
        title= data['title'],
        description= data['description'],
        start_time=datetime.fromisoformat(data['start_time'].replace('Z', '+00:00')),
        end_time=datetime.fromisoformat(data['end_time'].replace('Z', '+00:00')),
        location=data.get('location'),
        color=data.get('color', 'indigo'),
        created_by=current_user.id)
    
    db.session.add(g_event)
    db.session.commit()
    return jsonify(g_event.to_dict()), 201

@api_events.route("/api/events/group_events/edit/<int:group_event_id>", methods = ["PUT", "GET"])
@login_required
def api_edit_group_event(group_event_id):
    g_event = db.session.get(GroupEvent, group_event_id)
    if not g_event:
        return jsonify({"error": "Event not found"}), 404
    group = db.session.get(Group, g_event.group_id)
    if not group.is_member():
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json()

    # VALIDATE input fields
    errors = _validate_event_data(data)
    if errors:
        return jsonify({"error": "; ".join(errors)}), 400

    
    
    # VALIDATE input fields
    # Required fields
    if not data.get('title') or not data.get('start_time') or not data.get('end_time'):
        return jsonify({"error": "Please fill in all required fields."}), 400
    
    # End time after start time
    start = datetime.strptime(data['start_time'], '%Y-%m-%dT%H:%M:%S.%fZ').time()
    end = datetime.strptime(data['end_time'], '%Y-%m-%dT%H:%M:%S.%fZ').time()
    if end <= start:
        return jsonify({"error": "End time must be after start time."}), 400
    
    
    # update the event details - again we should add some validation here but we'll assume the data is correct for now
    g_event.title = data['title']
    g_event.description = data.get('description', '')
    g_event.start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
    g_event.end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
    g_event.location = data.get('location')
    g_event.color = data.get('color') or 'indigo'
    db.session.commit()
    return jsonify(g_event.to_dict()), 200

@api_events.route("/api/events/group_events/delete/<int:group_event_id>", methods = ["DELETE"])
@login_required
def api_delete_group_event(group_event_id):
    g_event = db.session.get(GroupEvent, group_event_id)
    if not g_event:
        return jsonify({"error": "Event not found"}), 404
    group = db.session.get(Group, g_event.group_id)
    if not group.is_member():
        return jsonify({"error": "Unauthorised"}), 403
    
    # Unlike events, all group events are custom.
    # So there will be no check for ical events here :)

    db.session.delete(g_event)
    db.session.commit()
    return jsonify({"message": "Group Event deleted"}), 200