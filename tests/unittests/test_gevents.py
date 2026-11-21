import unittest
from datetime import date, datetime, time, timezone

from app import create_app, db
from app.config import TestConfig
from app.models import Friendship, GroupEvent, Group, User


class GroupEventTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestConfig())
        self.app.config['WTF_CSRF_ENABLED'] = False # Disables CSRF during tests
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.populate_db()
        self.client = self.app.test_client()
        
        self.login()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
            
        # closes all SQLite connections (added due to ResourceWarning: unclosed database...)
        db.engine.dispose()
    
        self.app_context.pop()
        self.app = None
        self.app_context = None

    def populate_db(self): # Uses implemented login, group creation for convenience.
        self.user = User(username='mainuser', email='mainuser@example.com')
        self.user.password = 'Password1!'
        self.other_user1 = User(username='groupguy1', email='otheruser@example.com')
        self.other_user1.password = 'Password1!'
        self.other_user2 = User(username='groupguy2', email='asd123@example.com')
        self.other_user2.password = 'Password1!'

        db.session.add(self.user)
        db.session.add(self.other_user1)
        db.session.add(self.other_user2)
        db.session.commit()

        friends = [self.other_user1, self.other_user2] # implemented as loop for scalability if want to test more friends
        for friend in friends:
            friendship = Friendship(sender_id=self.user.id, recipient_id=friend.id, status='accepted', created_at=db.func.now())
            db.session.add(friendship)
        db.session.commit()

        self.group = Group(group_name='coolgroup', members=[self.user, self.other_user1, self.other_user2])
        self.secret_group = Group(group_name='Secret group without You', members=[self.other_user1, self.other_user2])
        db.session.add(self.secret_group)
        db.session.add(self.group)
        db.session.commit()
        self.populate_events()

    def login(self):
        with self.client.session_transaction() as session:
            session['_user_id'] = str(self.user.id)
            session['_fresh'] = True

    def populate_events(self):
        self.gev = GroupEvent(
            group_id= self.group.id,
            title='Coffee Meet Up', 
            description='Obligatory hanging out :)',
            start_time=datetime(2026, 5, 13, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 5, 13, 11, 0, tzinfo=timezone.utc),
            location='Maccas',
            color = 'indigo',
            created_by = self.user.id)
        self.altgev = GroupEvent(
            group_id= self.secret_group.id,
            title='McDs Run', 
            description='Happy meal time :)',
            start_time=datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 8, 11, 13, 0, tzinfo=timezone.utc),
            location='Maccas',
            color = 'orange',
            created_by = self.user.id
        )
        db.session.add(self.gev)
        db.session.add(self.altgev)
        db.session.commit()

    # Test api_group_events, displaying all events for a group of users in group table (including group events.)
    def test_create_group_event(self):

        response = self.client.post(f'/api/events/group_events/create/{self.group.id}', json={
            "title": "Group Event Meeting",
            "description": "Discussion on how we'd implement group events",
            "start_time": "2024-07-01T14:00:00.000Z",
            "end_time": "2024-07-01T15:00:00.000Z",
            "location": "Barry J Library, Meeting Room 1",
            "color": "indigo"
        })
        assert response.status_code == 201
        assert response.json['title'] == "Group Event Meeting"
        assert response.json['group_id'] == self.group.id
        assert GroupEvent.query.filter_by(title="Group Event Meeting", group_id=self.group.id).first() is not None

    def test_create_group_event_not_a_group(self):
        response = self.client.post(f'/api/events/group_events/create/123', json={
            "title": "Group Event Meeting",
            "description": "Discussion on how we'd implement group events",
            "start_time": "2024-07-01T14:00:00.000Z",
            "end_time": "2024-07-01T15:00:00.000Z",
            "location": "Barry J Library, Meeting Room 1",
            "color": "indigo"
        })
        assert response.status_code == 400
        assert response.json["Error"] == "Invalid group provided"
        assert GroupEvent.query.filter_by(title="Group Event Meeting").first() is None

    def test_create_group_event_not_a_group_member(self):
        response = self.client.post(f'/api/events/group_events/create/{self.secret_group.id}', json={
            "title": "Gossip about you!",
            "description": "Discussion on how we'd implement group events",
            "start_time": "2024-07-01T14:00:00.000Z",
            "end_time": "2024-07-01T15:00:00.000Z",
            "location": "Mcdonalds",
            "color": "indigo"
        })
        assert response.status_code == 403
        assert response.json["Error"] == "You're not apart of this group!"
        assert GroupEvent.query.filter_by(title="Gossip about you!").first() is None

    def test_create_group_event_validate_input(self):
        # The create route uses the validate event data function from event creation route, so just checks the function is implemented and is shorter.
        # All the rest of the group event route utilise the same function, so this is only tested once here.
        response = self.client.post(f'/api/events/group_events/create/{self.group.id}', json={
                    "title": "Group Event Meeting",
                    "description": "Discussion on how we'd implement group events",
                    "start_time": "2024-07-01T15:00:00.000Z",
                    "end_time": "2024-07-01T14:00:00.000Z",
                    "location": "Barry J Library, Meeting Room 1",
                    "color": "aqua"
                })

        assert response.status_code == 400

    def test_edit_group_event(self):
        response = self.client.put(f'/api/events/group_events/edit/{self.gev.id}', json={
            'title': 'Coffee Meet Up', 
            'description': 'Fun hang out :)',
            "start_time": "2024-07-01T15:00:00.000Z",
            "end_time": "2024-07-01T16:00:00.000Z",
            'location': 'Hungry Jacks',
            'color': 'emerald'
        })
        assert response.status_code == 200
        assert response.json['title'] == 'Coffee Meet Up'
        assert response.json['description'] == 'Fun hang out :)'
        assert response.json['startTime'] == '2024-07-01T15:00:00+00:00'
        assert response.json['endTime'] == '2024-07-01T16:00:00+00:00'
        assert response.json['location'] == 'Hungry Jacks'
        assert response.json['color'] == 'emerald'

        gev = self.gev.to_dict()
        assert gev['title'] == response.json['title']
        assert gev['description'] == response.json['description']
        assert gev['startTime'] == response.json['startTime']
        assert gev['endTime'] == response.json['endTime']
        assert gev['location'] == response.json['location']
        assert gev['color'] == response.json['color']

    def test_edit_group_event_does_not_exist(self):
        response = self.client.put(f'/api/events/group_events/edit/1234', json={
            'title': 'Coffee Meet Up', 
            'description': 'Fun hang out :)',
            "start_time": "2024-07-01T15:00:00.000Z",
            "end_time": "2024-07-01T16:00:00.000Z",
            'location': 'Hungry Jacks',
            'color': 'emerald'
        })
        assert response.status_code == 404
        assert response.json['error'] == "Event not found"

    def test_edit_group_event_not_a_member(self):
        response = self.client.put(f'/api/events/group_events/edit/{self.altgev.id}', json={
            'title': 'Mcdonalds Run', 
            'description': 'We love happy meals.',
            "start_time": "2027-02-03T12:00:00.000Z",
            "end_time": "2027-02-03T13:00:00.000Z",
            'location': 'Mcdonalds',
            'color': 'orange'
        })
        assert response.status_code == 403
        assert response.json['error'] == "Unauthorized"

        # Make sure the changes didn't get made into db.
        assert self.altgev.title == 'McDs Run'
        assert self.altgev.description == 'Happy meal time :)'
        assert self.altgev.location == 'Maccas'

    def test_delete_group_event(self):
        response = self.client.delete(f'/api/events/group_events/delete/{self.gev.id}')

        assert response.status_code == 200
        assert response.json['message'] == "Group Event deleted"

        assert GroupEvent.query.filter_by(title="Coffee Meet Up").first() is None

    def test_delete_group_event_not_found(self):
        response = self.client.delete(f'/api/events/group_events/delete/12345')

        assert response.status_code == 404
        assert response.json['error'] == "Event not found"

    def test_delete_group_event_not_a_member(self):
        response = self.client.delete(f'/api/events/group_events/delete/{self.altgev.id}')

        assert response.status_code == 403
        assert response.json['error'] == "Unauthorised"

        assert GroupEvent.query.filter_by(title='McDs Run', id=self.altgev.id).first() is not None