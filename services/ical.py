import requests
from datetime import datetime, time
from icalendar import Calendar as ICalendar
import ipaddress, socket
from urllib.parse import urlparse

from extensions import db
from models import Event, Calendar
# For now we just use the first user in the database. 
# When we have session/auth context, we'll use that instead.
user_id = 1 # TODO: replace with session user


#sanitise input and check that the URL is safe to fetch from.
# prefevent ssrf attack : no funky ip stuff
def _is_safe_url(url):
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        return False
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(hostname))
        return ip.is_global and not ip.is_loopback and not ip.is_private
    except (socket.gaierror, ValueError):
        return False
    
# Validate the URL before doing anything

def validate_url(url):
    """
    Check that the URL is a non-empty string that starts with https://.
    Returns an error string if invalid, or None if the URL looks fine.
    """
    # Basic validation — we could be more strict 
    if not url or not isinstance(url, str):
        return "A URL is required."

    # Must start with https://
    if not url.startswith("https://"):
        return "URL must start with https://"

    # Check if the URL is safe
    if not _is_safe_url(url):
        return "URL is not safe."

    return None  # no error

# store the users ical feed URL in the database 
def store_ical_url(url):
    """
    Store the user's iCal feed URL in the database. This allows us to fetch and update events later.
    """
    # Check if the user already has a calendar, for now we only support one calendar per user. 
    # If they do, update the URL if differnet
    # if the url is the same, fetch the same url again but with an update
    calendar = Calendar.query.filter_by(user_id=user_id).first()
    if calendar:
        calendar.ical_url = url
        has_calendar = True
    else:
        calendar = Calendar(user_id=user_id, ical_url=url)
        db.session.add(calendar)
        has_calendar = False
    db.session.commit()
    return has_calendar  # no error


# Fetch the raw iCal data from the URL

def fetch_ical_events(url):
    """
    Download the iCal feed from the given URL and return a list of VEVENT components.
    Raises an exception if the request fails or the content cannot be parsed.
    """
    # max size
    MAX_BYTES = 10 * 1024 * 1024  # 10 MB can fit something like ~5,000–20,000 events.
    # Use requests to fetch the content. We set a timeout
    response = requests.get(url, timeout=10)
    # Check for HTTP errors
    response.raise_for_status()
    # content too big
    if response.headers.get('Content-Length') and int(response.headers['Content-Length']) > MAX_BYTES:
        raise ValueError("The iCal feed is too large to process.")
    # Parse the iCal content using icalendar. This will give us a Calendar object with all the components.
    calendar = ICalendar.from_ical(response.content)

    # Walk the calendar and collect only VEVENT components
    return [component for component in calendar.walk() if component.name == "VEVENT"]


# Convert a single VEVENT into a plain dict

def parse_ical_event(component):
    """
    Convert one iCal VEVENT component into a dict matching our Event model's fields.

    iCal DTSTART/DTEND values can be either a date or a datetime.
    - If it's a datetime, we split it into date + time.
    - If it's a date only (all-day event), we default to 00:00 start and 23:59 end.
    """
    dtstart = component.get("DTSTART").dt
    dtend   = component.get("DTEND").dt

    # Handle both date and datetime cases for start and end times
    if isinstance(dtstart, datetime):
        event_date = dtstart.date()
        start_time = dtstart.time().replace(tzinfo=None)  # strip timezone — store as local time
    else:
        event_date = dtstart          # already a date object
        start_time = time(0, 0)       # all-day event — default to midnight

    # For the end time, if it's a datetime we take the time part. If it's a date, we default to 23:59 to represent the end of the day.
    if isinstance(dtend, datetime):
        end_time = dtend.time().replace(tzinfo=None)
    else:
        end_time = time(23, 59)       # all-day event — default to end of day

    # Now we build a dict with the fields we need for our Event model. We also handle missing fields and convert them to strings.
    return {
        "title":       str(component.get("SUMMARY", "Untitled")),
        "description": str(component.get("DESCRIPTION", "")) or None,
        "date":        event_date,
        "start_time":  start_time,
        "end_time":    end_time,
        "location":    str(component.get("LOCATION", "")) or None,
        "ical_uid":    str(component.get("UID", "")),
        "ical_id":    calendar_id,  # link to the calendar this event came from
    }


# Persist the parsed events to the database

def save_events_to_db(parsed_events):
    """
    Save a list of parsed event dicts to the database, linked to the given user.
    Returns the number of events saved.
    """
    for event_data in parsed_events:
        event = Event(user_id=user_id, **event_data)
        db.session.add(event)
    
    # Update the synced_at timestamp on the user's calendar
    Calendar.query.filter_by(user_id=user_id).update({"synced_at": datetime.now()})

    db.session.commit()
    return len(parsed_events)

# just update db events
def update_events_in_db(parsed_events):
    """
    Update existing events in the database based on their ical_id. If an event with the same ical_id, user_id and ical_id exists, update its details. If not, create a new event.
    Returns a tuple: (created_count, updated_count)
    """
    created_count = 0
    updated_count = 0

    for event_data in parsed_events:
        existing_event = Event.query.filter_by(user_id=user_id, ical_id=event_data['ical_id'], ical_uid=event_data['ical_uid']).first()
        if existing_event:
            # Update the existing event's details
            existing_event.title = event_data['title']
            existing_event.description = event_data['description']
            existing_event.date = event_data['date']
            existing_event.start_time = event_data['start_time']
            existing_event.end_time = event_data['end_time']
            existing_event.location = event_data['location']
            existing_event.color = event_data.get('color', 'indigo')
            updated_count += 1
        else:
            # Create a new event
            new_event = Event(user_id=user_id, **event_data)
            db.session.add(new_event)
            created_count += 1
    
    # Update the synced_at timestamp on the user's calendar
    Calendar.query.filter_by(user_id=user_id).update({"synced_at": datetime.now()})

    db.session.commit()
    return created_count, updated_count

# Main Function called by the API route

def import_ical(url):
    """
    Orchestrates the full import pipeline:
      1. Validate the URL
      2. Fetch and parse the iCal feed
      3. Convert each event to our format
      4. Save everything to the database

    Returns a tuple: (result, error)
      - On success: ({'imported': <count>}, None)
      - On failure: (None, '<error message>')
    """
    # 1. Validate inputs
    url_error = validate_url(url)
    if url_error:
        return None, url_error

    has_calendar = store_ical_url(url)  # store the URL and get whether it's a new calendar or an update
    # 2. Fetch iCal events from the URL
    try:
        ical_events = fetch_ical_events(url)
    # We catch both network errors (requests.exceptions.RequestException) and parsing errors
    except requests.exceptions.RequestException as e:
        return None, f"Could not fetch the iCal feed: {e}"
    except Exception as e:
        return None, f"Could not parse the iCal feed: {e}"
    # If the feed was fetched successfully but contained no events, error
    if not ical_events:
        return None, "The iCal feed contained no events."

    # 3. Parse each event — skip any that are malformed
    # create a list to hold the successfully parsed events
    parsed_events = []
    for component in ical_events:
        try:
            parsed_events.append(parse_ical_event(component))
        except Exception:
            continue  # skip this event and move on

    if not parsed_events:
        return None, "No valid events could be parsed from the iCal feed."

    # 4. Save to the database
    if has_calendar:  # if the user already had a calendar, we update existing events instead of creating new ones
        try:
            created_count, updated_count = update_events_in_db(parsed_events)
        except Exception as e:
            return None, f"Failed to update events in the database: {e}"
        return {"created": created_count, "updated": updated_count}, None
    elif not has_calendar:
        try:
            count = save_events_to_db(parsed_events)
        except Exception as e:
            return None, f"Failed to save events to the database: {e}"
        return {"imported": count}, None
