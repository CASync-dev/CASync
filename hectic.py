"""
hectic.py — seeds a varied dataset for stress-testing the group schedule view.

Creates (or refreshes):
- ~38 'hectic_*' users with varied weekly schedules
- 3 groups, sized differently so we can see how the view scales:
    'Low Clash'  -> 3 users + liam   (small group)
    'Mid Clash'  -> 10 users + liam  (medium group)
    'High Clash' -> 25 users + liam  (large group)
- ~4 weeks of events around today's date

Each user picks a different handful of weekly slots from a large pool covering
lectures, labs, tutorials, work shifts, gym sessions, club meetings, study
blocks, social events, etc. — so no two users look the same. Clashes happen
naturally from random overlap, not by design.

liam is preserved if already in the DB; his events inside the seed window are
replaced with a known baseline schedule.

Usage:
    python hectic.py
"""
import random
from datetime import date, time, timedelta

from app import app, db
from app.models import User, Event, Group

DEFAULT_PASSWORD = 'password123'
SEED = 42

TODAY = date.today()
RANGE_START = TODAY - timedelta(days=14)
RANGE_START -= timedelta(days=RANGE_START.weekday())
RANGE_DAYS = 28
RANGE_END = RANGE_START + timedelta(days=RANGE_DAYS - 1)

COLORS = [
    'indigo', 'blue', 'emerald', 'red', 'amber', 'purple',
    'pink', 'teal', 'rose', 'cyan', 'orange', 'lime', 'sky', 'violet',
]

# Pool of weekly slot templates: (weekday 0=Mon, start_hour, end_hour, title, location)
SLOT_POOL = [
    # Monday
    (0,  7,  8, 'Morning Run',             'UWA Oval'),
    (0,  8, 10, 'Linear Algebra Lecture',  'MATH: [G33] Weatherburn LT'),
    (0,  9, 11, 'Algorithms Lecture',      'CSSE: [1.24] Ross LT'),
    (0, 10, 12, 'Microeconomics Lecture',  'BUSN: [105] Business Bldg'),
    (0, 12, 13, 'Lunch with Tutor',        'Guild Cafe'),
    (0, 13, 15, 'Physics Lab',             'PHYS: [G15] Physics Lab 2'),
    (0, 14, 16, 'Agile Web Dev Lecture',   'ENGL: [G12] Lecture Theatre'),
    (0, 15, 17, 'History Tutorial',        'ARTS: [2.05] Seminar Room'),
    (0, 17, 19, 'Soccer Practice',         'UWA Sports Park'),
    (0, 19, 21, 'Dinner with Family',      'Home'),
    # Tuesday
    (1,  7,  8, 'Yoga',                    'UWA Sports Centre'),
    (1,  8, 10, 'Calculus Tutorial',       'MATH: [1.12] Tutorial Room'),
    (1,  9, 11, 'Chemistry Lecture',       'CHEM: [G05] Bayliss LT'),
    (1, 10, 12, 'Databases Lecture',       'CSSE: [G09] Fay Gale Studio'),
    (1, 11, 13, 'Philosophy Seminar',      'ARTS: [3.21] Seminar Room'),
    (1, 12, 14, 'Work Shift',              'Reid Library Help Desk'),
    (1, 13, 15, 'Statistics Lecture',      'MATH: [G23] Stats LT'),
    (1, 14, 16, 'Group Project Meeting',   'Reid Library Study Room 3'),
    (1, 15, 17, 'Reading Group',           'Reid Library Quiet Floor'),
    (1, 18, 20, 'Climbing Gym',            'Rockface Climbing'),
    # Wednesday
    (2,  8, 10, 'Gym',                     'UWA Sports Centre'),
    (2,  9, 10, 'Standup',                 'CSSE Foyer'),
    (2, 10, 12, 'Discrete Maths Lecture',  'MATH: [G33] Weatherburn LT'),
    (2, 11, 13, 'Networks Lecture',        'CSSE: [1.24] Ross LT'),
    (2, 12, 13, 'Club Meeting',            'Guild Village'),
    (2, 13, 15, 'AI Lab',                  'CSSE: [G15] Computer Lab'),
    (2, 14, 17, 'Internship Hours',        'Nano Solutions Office'),
    (2, 16, 18, 'Lab Time',                'CSSE: [G15] Computer Lab'),
    (2, 18, 20, 'Choir Rehearsal',         'UWA Music School'),
    # Thursday
    (3,  7,  9, 'Swim Squad',              'UWA Aquatic Centre'),
    (3,  9, 11, 'Algorithms Lab',          'CSSE: [G15] Computer Lab'),
    (3, 10, 12, 'Operating Systems Lec',   'CSSE: [1.24] Ross LT'),
    (3, 11, 13, 'Lunch Lecture',           'Guild Refectory'),
    (3, 13, 15, 'Independent Study',       'Reid Library'),
    (3, 14, 16, 'Marketing Lecture',       'BUSN: [105] Business Bldg'),
    (3, 15, 17, 'Agile Web Dev Tutorial',  'CSSE: [G09] Fay Gale Studio'),
    (3, 17, 19, 'Volunteering',            'Subiaco Community Centre'),
    (3, 19, 21, 'Trivia Night',            'Tavern UWA'),
    # Friday
    (4,  8, 10, 'Morning Run',             'Kings Park Loop'),
    (4,  9, 11, 'Software Eng. Lecture',   'CSSE: [1.24] Ross LT'),
    (4, 10, 12, 'Linguistics Lecture',     'ARTS: [G05] Arts LT'),
    (4, 12, 14, 'Capstone Studio',         'CSSE: [G09] Fay Gale Studio'),
    (4, 13, 15, 'Career Workshop',         'Guild Careers Centre'),
    (4, 14, 16, 'Robotics Club',           'Mechatronics Lab'),
    (4, 15, 17, 'Coffee Catchup',          'Hackett Cafe'),
    (4, 17, 19, 'Happy Hour',              'Tavern UWA'),
    (4, 19, 22, 'House Party',             "Friend's Place"),
    # Weekend
    (5,  9, 11, 'Farmers Market',          'Subiaco Markets'),
    (5, 10, 12, 'Surf Session',            'Cottesloe Beach'),
    (5, 14, 16, 'Study Session',           'Reid Library'),
    (5, 18, 20, 'Dinner with Friends',     'Northbridge'),
    (6, 10, 12, 'Brunch',                  'Mary Street Bakery'),
    (6, 13, 15, 'Hiking Trip',             'John Forrest National Park'),
    (6, 16, 18, 'Board Game Night',        'Good Games Perth'),
    (6, 19, 21, 'Movie Night',             'Luna Leederville'),
]

# liam's baseline: (weekday, start_hour, end_hour, title, location, color)
LIAM_SCHEDULE = [
    (0,  9, 11, 'Algorithms Lecture',     'CSSE: [1.24] Ross LT',         'indigo'),
    (0, 14, 16, 'Agile Web Dev Lecture',  'ENGL: [G12] Lecture Theatre',  'blue'),
    (1, 10, 12, 'Databases Lecture',      'CSSE: [G09] Fay Gale Studio',  'emerald'),
    (1, 13, 15, 'Statistics Lecture',     'MATH: [G23] Stats LT',         'amber'),
    (2, 11, 13, 'Networks Lecture',       'CSSE: [1.24] Ross LT',         'purple'),
    (3,  9, 11, 'Algorithms Lab',         'CSSE: [G15] Computer Lab',     'indigo'),
    (3, 15, 17, 'Agile Web Dev Tutorial', 'CSSE: [G09] Fay Gale Studio',  'blue'),
    (4, 12, 14, 'Capstone Studio',        'CSSE: [G09] Fay Gale Studio',  'red'),
    (5, 14, 16, 'Study Session',          'Reid Library',                 'teal'),
]


def weekday_dates(weekday):
    return [
        RANGE_START + timedelta(days=i)
        for i in range(RANGE_DAYS)
        if (RANGE_START + timedelta(days=i)).weekday() == weekday
    ]


def add_events(user, schedule):
    """schedule: iterable of (weekday, start_hour, end_hour, title, location, color)."""
    for weekday, sh, eh, title, location, color in schedule:
        for d in weekday_dates(weekday):
            db.session.add(Event(
                title=title,
                description=f'{title}\nLocation: {location}',
                date=d,
                start_time=time(sh, 0),
                end_time=time(eh, 0),
                location=location,
                color=color,
                user_id=user.id,
            ))


def varied_schedule(rng, n_events):
    """Pick n non-overlapping slots from the pool for one user."""
    pool = SLOT_POOL[:]
    rng.shuffle(pool)
    chosen = []
    taken = set()
    for weekday, sh, eh, title, location in pool:
        cells = {(weekday, h) for h in range(sh, eh)}
        if cells & taken:
            continue
        chosen.append((weekday, sh, eh, title, location, rng.choice(COLORS)))
        taken |= cells
        if len(chosen) >= n_events:
            break
    return chosen


def get_or_create_liam():
    liam = User.query.filter_by(username='liam').first()
    if not liam:
        liam = User(
            username='liam',
            email='24083063@student.uwa.edu.au',
            password=DEFAULT_PASSWORD,
        )
        db.session.add(liam)
        db.session.flush()
    return liam


def purge_previous_hectic_data(group_names):
    for g in Group.query.filter(Group.group_name.in_(group_names)).all():
        db.session.delete(g)
    for u in User.query.filter(User.username.like('hectic_%')).all():
        u.groups.clear()
        Event.query.filter_by(user_id=u.id).delete()
        db.session.delete(u)
    db.session.flush()


with app.app_context():
    rng = random.Random(SEED)

    group_specs = [
        ('Low Clash',   'low',   3),
        ('Mid Clash',   'mid',  10),
        ('High Clash',  'high', 25),
    ]
    group_names = [name for name, _, _ in group_specs]

    print(f'Seed window: {RANGE_START} -> {RANGE_END}')
    print('Purging previous hectic data...')
    purge_previous_hectic_data(group_names)

    liam = get_or_create_liam()

    Event.query.filter(
        Event.user_id == liam.id,
        Event.date >= RANGE_START,
        Event.date <= RANGE_END,
    ).delete(synchronize_session=False)
    db.session.flush()

    print("Seeding liam's baseline schedule...")
    add_events(liam, LIAM_SCHEDULE)

    for gname, prefix, n_members in group_specs:
        group = Group(group_name=gname)
        db.session.add(group)
        db.session.flush()
        group.members.append(liam)
        for i in range(n_members):
            uname = f'hectic_{prefix}_{i + 1:02d}'
            user = User(
                username=uname,
                email=f'{uname}@test.local',
                password=DEFAULT_PASSWORD,
            )
            db.session.add(user)
            db.session.flush()
            add_events(user, varied_schedule(rng, rng.randint(4, 9)))
            group.members.append(user)
        print(f'  "{gname}": {n_members} members + liam')

    db.session.commit()

    total_users = User.query.count()
    total_events = Event.query.count()
    print(f'Done. {total_users} users, {total_events} events.')
    print(f'Login as liam / {DEFAULT_PASSWORD} and open the Groups page to compare.')
