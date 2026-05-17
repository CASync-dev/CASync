import requests # for fetching the iCal feed from the URL
from datetime import datetime, date, time, timedelta, timezone # for handling date and time fields
from icalendar import Calendar as ICalendar # for parsing iCal data
import ipaddress, socket # for URL safety checks
from urllib.parse import urlparse # for URL parsing

from app import db
from app.models import Event, Calendar
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

    # Check if the URL is safe: we don't want to allow fetching from private IPs or localhost, to prevent SSRF attacks.
    if not _is_safe_url(url):
        return "URL is not safe."

    return None  # no error

# store the users ical feed URL in the database 
def store_ical_url(url, user_id):
    """
    Store the user's iCal feed URL in the database. This allows us to fetch and update events later.
    """
    # Check if the user already has a calendar of the same url, if so we update the existing calendar's URL and synced_at timestamp. 
    # If not, we create a new calendar entry for the user.
    calendar = Calendar.query.filter_by(user_id=user_id, ical_url=url).first()
    if calendar:
        calendar.synced_at = datetime.now(timezone.utc)
        has_calendar = True
        cal_id = calendar.id
    else:
        new_calendar = Calendar(user_id=user_id, ical_url=url, synced_at=datetime.now(timezone.utc))
        db.session.add(new_calendar)
        db.session.flush()  # populate new_calendar.id before commit
        cal_id = new_calendar.id
        has_calendar = False
    db.session.commit()
    return has_calendar, cal_id  # no error


# Fetch the raw iCal data from the URL

def fetch_ical_events(url):
    """
    Download the iCal feed from the given URL and return a list of VEVENT components.
    Raises an exception if the request fails or the content cannot be parsed.
    """
    # max size — ~5,000–20,000 events fits comfortably in 10 MB
    MAX_BYTES = 10 * 1024 * 1024
    # Stream the response so we can enforce the size limit on actual bytes received,
    # not just the Content-Length header (which servers can omit or lie about)
    with requests.get(url, timeout=10, stream=True) as response:
        # Check for HTTP errors
        response.raise_for_status()
        chunks = []
        received = 0
        for chunk in response.iter_content(chunk_size=65536):
            received += len(chunk)
            if received > MAX_BYTES:
                raise ValueError("The iCal feed is too large to process.")
            chunks.append(chunk)
        raw = b"".join(chunks)
    # Parse the iCal content using icalendar. This will give us a Calendar object with all the components.
    calendar = ICalendar.from_ical(raw)

    # Walk the calendar and collect only VEVENT components
    return [component for component in calendar.walk() if component.name == "VEVENT"]


# Convert a single VEVENT into a plain dict

def _to_utc_datetime(value, end_of_day=False):
    """
    Coerce an iCal DTSTART/DTEND value (date or datetime, naive or aware) to a
    UTC-aware datetime. Bare dates become midnight UTC; if end_of_day is True
    they become the start of the next day so all-day events span the full day.
    """
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    # Bare date — all-day event.
    if end_of_day:
        value = value + timedelta(days=1)
    return datetime.combine(value, time(0, 0), tzinfo=timezone.utc)


def parse_ical_event(component, user_id, cal_id):
    """
    Convert one iCal VEVENT component into a dict matching our Event model's fields.
    Heavily utilises icalnder package.

    DTSTART/DTEND become full UTC datetimes so multi-day events are preserved.
    All-day events (DTSTART is a bare date) get midnight UTC for start and
    midnight UTC of the following day for end.
    """
    dtstart = component.get("DTSTART").dt
    dtend   = component.get("DTEND").dt

    start_time = _to_utc_datetime(dtstart)
    end_time   = _to_utc_datetime(dtend, end_of_day=not isinstance(dtend, datetime))

    return {
        "title":       str(component.get("SUMMARY", "Untitled")),
        "description": str(component.get("DESCRIPTION", "")) or None,
        "start_time":  start_time,
        "end_time":    end_time,
        "location":    str(component.get("LOCATION", "")) or None,
        "ical_uid":    str(component.get("UID", "")),
        "ical_id":    cal_id,  # link to the calendar this event came from
    }


# Persist the parsed events to the database

def save_events_to_db(parsed_events, user_id, cal_id):
    """
    Save a list of parsed event dicts to the database, linked to the given user.
    Returns the number of events saved.
    """
    for event_data in parsed_events:
        event = Event(user_id=user_id, **event_data)
        db.session.add(event)
    
    # Update the synced_at timestamp on the user's calendar
    Calendar.query.filter_by(user_id=user_id, id=cal_id).update({"synced_at": datetime.now(timezone.utc)})

    db.session.commit()
    return len(parsed_events)

# just update db events
def update_events_in_db(parsed_events, user_id, cal_id):
    """
    Update existing events in the database based on their ical_id. If an event with the same ical_id, user_id and ical_id exists, update its details. If not, create a new event.
    Returns a tuple: (created_count, updated_count)
    """
    created_count = 0
    updated_count = 0

    for event_data in parsed_events:
        # Try to find an existing event with the same user_id, ical_id and ical_uid
        existing_event = Event.query.filter_by(user_id=user_id, ical_id=event_data['ical_id'], ical_uid=event_data['ical_uid']).first()
        if existing_event:
            # If the event already exists, we check if any of the details have changed. If they have, we update the existing event.
            new_color = event_data.get('color', None)
            if ( # we only update if something has actually changed, to avoid unnecessary database writes
                existing_event.title != event_data['title']
                or existing_event.description != event_data['description']
                or existing_event.start_time != event_data['start_time']
                or existing_event.end_time != event_data['end_time']
                or existing_event.location != event_data['location']
                or existing_event.color != new_color
            ):
                # Update the existing event with the new details
                existing_event.title = event_data['title']
                existing_event.description = event_data['description']
                existing_event.start_time = event_data['start_time']
                existing_event.end_time = event_data['end_time']
                existing_event.location = event_data['location']
                existing_event.color = new_color
                updated_count += 1
        else:
            # Create a new event
            new_event = Event(user_id=user_id, **event_data)
            db.session.add(new_event)
            created_count += 1
    
    # Update the synced_at timestamp on the user's calendar
    Calendar.query.filter_by(user_id=user_id, id=cal_id).update({"synced_at": datetime.now(timezone.utc)})

    db.session.commit()
    return created_count, updated_count

# Main Function called by the API route

def import_ical(url, user_id):
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

    has_calendar, cal_id = store_ical_url(url, user_id)  # store the URL and get whether it's a new calendar or an update
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
            parsed_events.append(parse_ical_event(component, user_id, cal_id))
        except Exception:
            continue  # skip this event and move on

    if not parsed_events:
        return None, "No valid events could be parsed from the iCal feed."

    # 4. Save to the database
    if has_calendar:  # if the user already had a calendar, we update existing events instead of creating new ones
        try:
            created_count, updated_count = update_events_in_db(parsed_events, user_id, cal_id)
        except Exception as e:
            return None, f"Failed to update events in the database: {e}"
        return {"created": created_count, "updated": updated_count}, None
    else:
        try:
            count = save_events_to_db(parsed_events, user_id, cal_id)
        except Exception as e:
            return None, f"Failed to save events to the database: {e}"
        return {"imported": count}, None
