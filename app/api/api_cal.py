from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import delete
from app import db
from app.models import Calendar, Event
from services.ical import import_ical

api_cal = Blueprint('api_cal', __name__)

# -- API CALENDAR ROUTES
@api_cal.route("/api/calendars/")
@login_required
def api_calendars():
    user_id = current_user.id
    calendars = Calendar.query.where(Calendar.user_id == user_id).all()
    return jsonify([{"id": c.id, "ical_url": c.ical_url, "synced_at": c.synced_at.isoformat()} for c in calendars])

@api_cal.route("/api/import-ical/", methods=["POST"])
@login_required
def api_import_ical():
    """
    POST /api/import-ical/
    Body: { "url": "<ical feed url>" }

    Passes the URL and user to services/ical.py which validates, fetches,
    parses, and saves the events. Returns 200 on success or 400 on failure.
    """
    # Get JSON data from the request body
    data = request.get_json(silent=True)
    user_id = current_user.id
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

@api_cal.route("/api/sync-cal/", methods=["POST"])
@login_required
def api_sync_cal():
    """
    POST /api/sync-cal/

    Gets all calendars for the user, then for each calendar fetches the latest events from the iCal 
    feed and updates the database accordingly. This allows us to keep imported events up to date 
    with any changes in the original calendar.
    """
    user_id = current_user.id
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

@api_cal.route("/api/remove-cal/", methods=["POST"])
@login_required
def api_remove_cal():
    '''
    POST /api/remove-cal/

    Removes iCal link from user.
    '''
    data = request.get_json()
    if 'id' not in data or len(data['id']) < 1:
        return jsonify({"error": "Invalid iCal Link"})
    icalid = data['id']
    user_id = current_user.id
    # Check in case somehow the id does not belong to a calendar the user has.
    cal = Calendar.query.where(Calendar.user_id == user_id and Calendar.id == icalid)
    if not cal:
        return jsonify({"error": "Something's gone wrong!"})
    
    # Actual deletion of ical
    # First deletes events then the iCal link
    # 1. Remove events associated with the ical link
    delEvents = delete(Event).where(Event.ical_id == icalid)
    db.session.execute(delEvents)

    # 2. Remove Calendar with the link
    delCal = delete(Calendar).where(Calendar.user_id == user_id and Calendar.id == icalid)
    db.session.execute(delCal)

    # 3. Commit and return with success.
    db.session.commit()
    return jsonify({"success": "iCal successfully removed."})