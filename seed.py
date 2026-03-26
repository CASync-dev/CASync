import json
from datetime import date, time
from app import app, db
from models import User, Event


def parse_date(s):
    return date.fromisoformat(s)  # "2026-03-26" -> date object


def parse_time(s):
    h, m = s.split(':')
    return time(int(h), int(m))  # "11:00" -> time object


with app.app_context():
    db.create_all()

    # Skip if already seeded
    if User.query.first():
        print('DB already seeded, skipping.')
        exit()

    # Create the test user
    liam = User(username='liam', email='liam@student.uwa.edu.au')
    db.session.add(liam)
    db.session.flush()  # gives liam an id before attaching events

    # Load events from the mock data file and insert them
    with open('static/data/events.json') as f:
        events = json.load(f)

    for e in events:
        db.session.add(Event(
            title      = e['title'],
            date       = parse_date(e['date']),
            start_time = parse_time(e['startTime']),
            end_time   = parse_time(e['endTime']),
            location   = e.get('location'),
            color      = e.get('color', 'indigo'),
            user_id    = liam.id,
        ))

    db.session.commit()
    print(f'Seeded {len(events)} events for user "{liam.username}".')
