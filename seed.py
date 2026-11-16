# Note: This is an old seed.py file that does not work in the current version of CASync. Please use seed_demo.py instead.
import json
from datetime import date, datetime, time, timezone
from app import app, db
from app.models import User, Event
import sys


def parse_datetime(date_str, time_str):
    """Combine a YYYY-MM-DD date and HH:MM time into a UTC-aware datetime."""
    h, m = time_str.split(':')
    return datetime.combine(
        date.fromisoformat(date_str),
        time(int(h), int(m)),
        tzinfo=timezone.utc,
    )


with app.app_context():
    # Skip if already seeded
    if User.query.first():
        print('DB already seeded, skipping.')
        exit(0)

    # Create the test users
    DEFAULT_PASSWORD = 'password123'
    users = []
    liam = User(username='liam', email='24083063@student.uwa.edu.au', password=DEFAULT_PASSWORD)
    sze = User(username='sze', email='24214052@student.uwa.edu.au', password=DEFAULT_PASSWORD)
    kelly = User(username='kelly', email='24540356@student.uwa.edu.au', password=DEFAULT_PASSWORD)
    tehei = User(username='tehei', email='24467332@student.uwa.edu.au', password=DEFAULT_PASSWORD)
    users.extend([liam, sze, kelly, tehei])
    for user in users:
        db.session.add(user)
    # we have to sort of 'stage' the users before we can add events for them
    db.session.flush()  # gives users ids before attaching events

    # Load events from the mock data file and insert them
    with open('static/data/events.json') as f:
        events = json.load(f)

    # if the script is run with the argument 'seed:events':
    #   it will also seed events for each user. Otherwise,
    #   it will just seed the users without any events.
    if len(sys.argv) > 1 and sys.argv[1] == 'seed:events':
        print('Seeding User Events: ')
        for e in events:
            for user in users:

                db.session.add(Event(
                    title      = e['title'],
                    start_time = parse_datetime(e['date'], e['startTime']),
                    end_time   = parse_datetime(e['date'], e['endTime']),
                    location   = e.get('location'),
                    color      = e.get('color', 'indigo'),
                    user_id    = user.id,
            ))
    else:
        print('Seeding without events (users only).')

    db.session.commit()
    users_list = []
    for user in users:
        users_list.append(user.username)
    print(f'Seeded {len(users)} users: {", ".join(users_list)}' + f'with {len(events)} events each.')
