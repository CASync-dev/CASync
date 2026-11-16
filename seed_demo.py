"""
Demo seed script.

Creates:
  - mathew (lecturer) with manual events
  - tehei, liam, szeying, kelly — each with their UWA iCal feeds imported
    via the same import_ical() pipeline used by the app

Friendships:
  - mathew <-> tehei    : accepted
  - mathew <-> szeying  : accepted
  - tehei  <-> szeying  : accepted
  - kelly  -> mathew    : pending
  - liam                : no friendship (not friends yet)

Group: mathew, tehei, szeying

"""

import sys
from datetime import datetime, timezone

from app import create_app, db
from app.config import DeploymentConfig
from app.models import User, Event, Friendship, Group
from services.ical import import_ical

ICAL_URLS = {
    'tehei':   'https://apps.cas.uwa.edu.au/even/rest/calendar/ical/7570d76f-9ffc-4c04-af13-73b78ffe1701',
    'liam':    'https://apps.cas.uwa.edu.au/even/rest/calendar/ical/fc7191ca-3391-4caa-8234-5378b0b73225',
    'szeying': 'https://apps.cas.uwa.edu.au/even/rest/calendar/ical/de4902f5-e3a7-485a-a248-04b5dc0548d3',
    'kelly':   'https://apps.cas.uwa.edu.au/even/rest/calendar/ical/f82dadf2-026e-44c4-94be-9f2c2aa2f533',
}

DEFAULT_PASSWORD = 'password123'


def utc(year, month, day, hour, minute=0):
    """Return a UTC-aware datetime. Caller is responsible for Perth→UTC offset."""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


flask_app = create_app(DeploymentConfig())

with flask_app.app_context():
    if User.query.first():
        print('DB already seeded — skipping. Drop/reset the DB first to re-seed.')
        sys.exit(0)

    # ── Users ──────────────────────────────────────────────────────────────────────
    mathew  = User(username='mathew', email='mathew.daggitt@uwa.edu.au', password=DEFAULT_PASSWORD, email_confirmed = True)
    tehei   = User(username='tehei', email='24467332@student.uwa.edu.au', password=DEFAULT_PASSWORD, email_confirmed = True)
    liam    = User(username='liam', email='24083063@student.uwa.edu.au', password=DEFAULT_PASSWORD, email_confirmed = True)
    szeying = User(username='szeying', email='24214052@student.uwa.edu.au', password=DEFAULT_PASSWORD, email_confirmed = True)
    kelly   = User(username='kelly', email='24540356@student.uwa.edu.au', password=DEFAULT_PASSWORD, email_confirmed = True)

    all_users = [mathew, tehei, liam, szeying, kelly]
    for u in all_users:
        db.session.add(u)
    db.session.flush()  # assign IDs before attaching events

    # ── Mathew's events ────────────────────────────────────────────────────────────
    # All times converted to UTC (Perth = UTC+8, so subtract 8 h).
    # "tomorrow" is Monday 18 May 2026.
    mathew_events = [
        # Monday 18 May
        Event(
            title='Grading too many projects',
            description='Marking CITS3403 Agile Web Development project submissions.',
            start_time=utc(2026, 5, 18, 0, 0),   # 8:00 am AWST
            end_time=utc(2026, 5, 18, 4, 0),      # 12:00 pm AWST
            location='Office — CS Building G.04',
            color='red',
            user_id=mathew.id,
        ),
        Event(
            title='CITS3403 Curriculum Review',
            description='Meeting with faculty to discuss course updates for next semester.',
            start_time=utc(2026, 5, 18, 5, 0),   # 1:00 pm AWST
            end_time=utc(2026, 5, 18, 6, 0),      # 2:00 pm AWST
            location='Engineering Lecture Theatre 1',
            color='indigo',
            user_id=mathew.id,
        ),
        # Tuesday 19 May
        Event(
            title='Faculty Meeting',
            description='Weekly school of computing staff meeting.',
            start_time=utc(2026, 5, 19, 2, 0),   # 10:00 am AWST
            end_time=utc(2026, 5, 19, 3, 0),      # 11:00 am AWST
            location='CS Building — Staff Room 2.14',
            color='blue',
            user_id=mathew.id,
        ),
        # Wednesday 20 May — specified time
        Event(
            title='Agile Web Development, Lecture-01',
            description='CITS3403 Lecture — Agile methodologies, project structure, and Flask fundamentals.',
            start_time=utc(2026, 5, 20, 8, 0),   # 4:00 pm AWST
            end_time=utc(2026, 5, 20, 10, 0),     # 6:00 pm AWST
            location='Social Sciences Lecture Theatre',
            color='green',
            user_id=mathew.id,
        ),
        # Thursday 21 May
        Event(
            title='Office Hours',
            description='Drop-in office hours for students to discuss project and course content.',
            start_time=utc(2026, 5, 21, 6, 0),   # 2:00 pm AWST
            end_time=utc(2026, 5, 21, 8, 0),      # 4:00 pm AWST
            location='Office — CS Building G.04',
            color='yellow',
            user_id=mathew.id,
        ),
        # Friday 22 May — specified time
        Event(
            title='Agile Web Development, LecTut-01',
            description='CITS3403 combined lecture-tutorial — hands-on session with Flask and SQLAlchemy.',
            start_time=utc(2026, 5, 22, 2, 0),   # 10:00 am AWST
            end_time=utc(2026, 5, 22, 4, 0),      # 12:00 pm AWST
            location='Computer Lab — CS Building 2.31',
            color='green',
            user_id=mathew.id,
        ),
        # Following Monday 25 May
        Event(
            title='CITS3403 Exam Review Session',
            description='Reviewing past exam papers with students ahead of the end-of-semester exam.',
            start_time=utc(2026, 5, 25, 3, 0),   # 11:00 am AWST
            end_time=utc(2026, 5, 25, 4, 0),      # 12:00 pm AWST
            location='Lecture Theatre 1.04',
            color='orange',
            user_id=mathew.id,
        ),
        Event(
            title='Research Paper Review',
            description='Reviewing and providing feedback on submitted research proposals.',
            start_time=utc(2026, 5, 26, 1, 0),   # 9:00 am AWST
            end_time=utc(2026, 5, 26, 3, 0),      # 11:00 am AWST
            location='Office — CS Building G.04',
            color='purple',
            user_id=mathew.id,
        ),
    ]

    for e in mathew_events:
        db.session.add(e)

    db.session.commit()
    print(f'Created {len(mathew_events)} events for mathew.')

    # ── iCal imports for the four students ────────────────────────────────────────
    ical_users = [
        (tehei,   ICAL_URLS['tehei']),
        (liam,    ICAL_URLS['liam']),
        (szeying, ICAL_URLS['szeying']),
        (kelly,   ICAL_URLS['kelly']),
    ]

    for user, url in ical_users:
        print(f'Importing iCal for {user.username}...', end=' ', flush=True)
        result, error = import_ical(url, user.id)
        if error:
            print(f'WARNING: {error}')
        else:
            count = result.get('imported') or result.get('created', 0)
            print(f'{count} events imported.')

    # ── Friendships ───────────────────────────────────────────────────────────────
    now = datetime.now(timezone.utc)
    friendships = [
        Friendship(sender_id=mathew.id,  recipient_id=tehei.id,   status='accepted', accepted_at=now),
        Friendship(sender_id=mathew.id,  recipient_id=szeying.id, status='accepted', accepted_at=now),
        Friendship(sender_id=tehei.id,   recipient_id=szeying.id, status='accepted', accepted_at=now),
        # Kelly has a pending request towards mathew
        Friendship(sender_id=kelly.id,   recipient_id=mathew.id,  status='pending'),
        # Liam has no friendship record with mathew
    ]
    for f in friendships:
        db.session.add(f)

    # ── Group: mathew, tehei, szeying ─────────────────────────────────────────────
    group = Group(group_name='Mathew, Tehei & Sze')
    group.members = [mathew, tehei, szeying]
    db.session.add(group)

    db.session.commit()

    print()
    print(f'Seeded {len(all_users)} users: {", ".join(u.username for u in all_users)}')
    print('Friendships:')
    print('  mathew <-> tehei   : accepted')
    print('  mathew <-> szeying : accepted')
    print('  tehei  <-> szeying : accepted')
    print('  kelly  -> mathew   : pending')
    print('  liam               : no friendship')
    print('Group: "Mathew, Tehei & Sze" (mathew, tehei, szeying)')
