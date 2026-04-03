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

    # Create the test users
    users = []
    liam = User(username='liam', email='24083063@student.uwa.edu.au')
    sze = User(username='sze', email='24214052@student.uwa.edu.au')
    kelly = User(username='kelly', email='24540356@student.uwa.edu.au')
    tehei = User(username='tehei', email='24467332@student.uwa.edu.au')
    users.extend([liam, sze, kelly, tehei])
    for user in users:
        db.session.add(user)
    # we have to sort of 'stage' the users before we can add events for them
    db.session.flush()  # gives users ids before attaching events

    # Load events from the mock data file and insert them
    with open('static/data/events.json') as f:
        events = json.load(f)

    
    for e in events:
        for user in users:

            db.session.add(Event(
                title      = e['title'],
                date       = parse_date(e['date']),
                start_time = parse_time(e['startTime']),
                end_time   = parse_time(e['endTime']),
                location   = e.get('location'),
                color      = e.get('color', 'indigo'),
                user_id    = user.id,
        ))

    db.session.commit()
    users_list = []
    for user in users:
        users_list.append(user.username)
    print(f'Seeded {len(users)} users: {", ".join(users_list)}' + f'with {len(events)} events each.')
