from datetime import date, datetime, time
import unittest
from flask import json, jsonify
from app import create_app, db
from app.config import TestConfig
from app.models import Event, Friendship, User

class FriendsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestConfig())
        self.app.config['WTF_CSRF_ENABLED'] = False # Disables CSRF during tests
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()
        self.populate_db()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        self.app = None
        self.app_context = None

    def populate_db(self):
        # ID increments
        user = User(username='gerald', email='sekai@hotmail.com') # userid = 1
        user.password = 'foo'
        friend = User(username='allen', email='friend@fun.net') # User to friend. id = 2
        friend.password = 'bar'
        db.session.add(user)
        db.session.add(friend)
        db.session.commit()
        with self.client.session_transaction() as session:
            session['_user_id'] = str(user.id)
            session['_fresh'] = True # Copied from Tehei's example.
        self.client.post('/login', data={'username': 'gerald', 'password': 'foo'})
        self.user = user

    def test_getuser(self):
        # Test wrong data being submitted to the api
        data = {'username':'bob'}
        response = self.client.post('/api/getusers', json=json.dumps(data), content_type="application/json")
        data = response.get_json()
        assert response.status_code == 400
        assert "Error" in data
        assert data["Error"] ==  "Invalid search"
        
        # Test no data associated with 'search'
        response = self.client.post('/api/getusers', json={
            'search': "",
        })
        assert response.status_code == 400
        data = response.get_json()
        assert data["Error"] ==  "Invalid search"

        # Test email; Does not exist
        response = self.client.post('/api/getusers', json={
            'search': "fakeemail@mail.com",
            'json': True
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
        assert data['results'] == 0

        # Test email; Is current users
        response = self.client.post('/api/getusers', json={
            'search': 'sekai@hotmail.com',
            'json': True
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
        assert data['results'] == 0

        # Test email; User exists

        response = self.client.post('/api/getusers', json={
            'search': 'friend@fun.net',
            'json': True
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
        assert data['results'] == [{'id': 2, 'pfp': 'https://www.gravatar.com/avatar/90dae26ca1e83875794c56b583a8f940?d=identicon&s=150', 'username': 'allen'}] # Don't know if this is the right format, check prior to merge

        # Test Username; user does not exist
        response = self.client.post('/api/getusers', json={
            'search': 'fakeuser',
            'json': True
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
        assert data['results'] == 0

        # Test username; Is current users
        response = self.client.post('/api/getusers', json={
            'search': 'gerald',
            'json': True
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
        assert data['results'] == 0

        # Test Username; User exists
        response = self.client.post('/api/getusers', json={
            'search': 'allen',
            'json': True
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
        assert data['results'] == [{'id': 2, 'pfp': 'https://www.gravatar.com/avatar/90dae26ca1e83875794c56b583a8f940?d=identicon&s=150', 'username': 'allen'}]

        # Request has already been made and shouldn't show up
        f = Friendship(sender_id=self.user.id, recipient_id=2, status='pending', created_at=db.func.now())
        db.session.add(f)
        db.session.commit()

        # Testing searching when a request has already been made (Email)--------------------------
        response = self.client.post('/api/getusers', json={
            'search': 'friend@fun.net',
            'json': True
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
        assert data['results'] == 0

        # User
        response = self.client.post('/api/getusers', json={
            'search': 'allen',
            'json': True
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
        assert data['results'] == 0
        # ----------------------------------------------------------------------------------------
        # Testing searching when request rejected.
        f.status = 'rejected'
        response = self.client.post('/api/getusers', json={
            'search': 'friend@fun.net',
            'json': True
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
        assert data['results'] == [{'id': 2, 'pfp': 'https://www.gravatar.com/avatar/90dae26ca1e83875794c56b583a8f940?d=identicon&s=150', 'username': 'allen'}]

        response = self.client.post('/api/getusers', json={
            'search': 'allen',
            'json': True
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
        assert data['results'] == [{'id': 2, 'pfp': 'https://www.gravatar.com/avatar/90dae26ca1e83875794c56b583a8f940?d=identicon&s=150', 'username': 'allen'}]

        # Testing searching when request accepted.
        f.status = 'accepted'
        f.accepted_at = db.func.now()
        response = self.client.post('/api/getusers', json={
            'search': 'friend@fun.net',
            'json': True
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
        assert data['results'] == 0

        # User
        response = self.client.post('/api/getusers', json={
            'search': 'allen',
            'json': True
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'results' in data
        assert data['results'] == 0

    def test_requestfriend(self):
        # Wrong data sent to api
        data = {'username':'bob'}
        response = self.client.post('/api/requestfriend', json=json.dumps(data), content_type="application/json")
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert data["error"] == "Invalid user_id"

        # User does not exist (Just in case somehow the webpage sends a non-existent user id)
        response = self.client.post('/api/requestfriend', json={
            'user_id': '50',
            'json': True
        })
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data
        assert data["error"] == "User not found"

        # User exists and no existing friend request exists between them.
        response = self.client.post('/api/requestfriend', json={
            'user_id': '2',
            'json': True
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert data['message'] == "Friend request sent to allen!"

        # User exists, and an existing friend request already exists
        response = self.client.post('/api/requestfriend', json={
            'user_id': '2',
            'json': True
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == "Friend request already pending"

        # User was rejected
        fq = Friendship.query.filter(Friendship.recipient_id == 2).first()
        fq.status = 'rejected'
        db.session.add(fq)
        db.session.commit()
        response = self.client.post('/api/requestfriend', json={
            'user_id': '2',
            'json': True
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert data['message'] == "Friend request sent to allen!"

        # User is already friends
        fq.status = 'accepted'
        fq.accepted_at = db.func.now()
        db.session.add(fq)
        db.session.commit()
        response = self.client.post('/api/requestfriend', json={
            'user_id': '2',
            'json': True
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == "You are already friends"
        
    def test_acceptfriend(self):
        # Creating the friendship explicitly incase previous test did not work. Probably not a good idea to rely on
        # Other apis for isolated tests :)
        new_request = Friendship(sender_id=2, recipient_id=self.user.id, status='pending', created_at=db.func.now()) # so that sender is our 'friend' user
        user = User(username="coolnotfriend", email="abcde@fg.com")
        user.password = 'foobar' # Not required but why not :')
        db.session.add(user)
        not_our_request = Friendship(sender_id=3, recipient_id=2, status='pending', created_at=db.func.now()) # Request that the current user did not send and not for.
        db.session.add(new_request)
        db.session.add(not_our_request)
        db.session.commit()

        request_id = new_request.id
        # Testing not valid id submitted
        response = self.client.post('/api/acceptfriend', json={
            'notrelated': 'to this api :(',
            'json': True
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'Error' in data
        assert data['Error'] == "Invalid request_id"

        # Testing request does not exist
        response = self.client.post('/api/acceptfriend', json={
            'request_id': 105,
            'json': True
        })
        assert response.status_code == 404
        data = response.get_json()
        assert 'Error' in data
        assert data['Error'] == 'No pending friend request found'

        # Testing request does not belong to us
        notourid = not_our_request.id
        response = self.client.post('/api/acceptfriend', json={
            'request_id': notourid,
            'json': True
        })
        assert response.status_code == 403
        data = response.get_json()
        assert 'Error' in data
        assert data['Error'] == "You can only accept friend requests sent to you"

        # Testing accept request (actuals)
        realfriendshipid = new_request.id
        response = self.client.post('/api/acceptfriend', json={
            'request_id': realfriendshipid,
            'json': True
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert data['message'] == "Friend request accepted from allen!"
        fdship = Friendship.query.filter(Friendship.id == request_id).first()
        assert fdship.status == 'accepted'

        # Testing request already accepted! So should not show up again.
        response = self.client.post('/api/acceptfriend', json={
            'request_id': realfriendshipid,
            'json': True
        })
        assert response.status_code == 404
        data = response.get_json()
        assert 'Error' in data
        assert data['Error'] == "No pending friend request found"


    def test_rejectfriend(self):
        # Creating the friendship explicitly incase previous test did not work. Probably not a good idea to rely on
        # Other apis for isolated tests :)
        new_request = Friendship(sender_id=2, recipient_id=self.user.id, status='pending', created_at=db.func.now()) # so that sender is our 'friend' user
        user = User(username="coolnotfriend", email="abcde@fg.com")
        user.password = 'foobar' # Not required but why not :')
        db.session.add(user)
        self.user = user
        not_our_request = Friendship(sender_id=3, recipient_id=2, status='pending', created_at=db.func.now()) # Request that the current user did not send and not for.
        db.session.add(new_request)
        db.session.add(not_our_request)
        db.session.commit()

        # Test required field not in json
        response = self.client.post('/api/rejectfriend', json={
            'notrelated': 'to this api :(',
            'json': True
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'Error' in data
        assert data['Error'] == "Invalid request_id"

        # Testing request does not exist
        response = self.client.post('/api/rejectfriend', json={
            'request_id': 105,
            'json': True
        })
        assert response.status_code == 404
        assert 'Error' in data
        data = response.get_json()
        assert data['Error'] == "No pending friend request found"

        # Testing rejecting a request where the current user is not the recipient
        notourid = not_our_request.id
        response = self.client.post('/api/rejectfriend', json={
            'request_id': notourid,
            'json': True
        })
        assert response.status_code == 403
        data = response.get_json()
        assert 'Error' in data
        assert data['Error'] == "You can only reject friend requests sent to you"

        # Testing actuals
        realfriendshipid = new_request.id
        response = self.client.post('/api/rejectfriend', json={
            'request_id': realfriendshipid,
            'json': True
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert data['message'] == "Friend request rejected."

        # Request rejected already, so can't reject again
        response = self.client.post('/api/rejectfriend', json={
            'request_id': realfriendshipid,
            'json': True
        })
        assert response.status_code == 404
        data = response.get_json()
        assert 'Error' in data
        assert data['Error'] == "No pending friend request found"

    def test_removefriend(self):
        # Test required field not in json
        response = self.client.post('/api/removefriend', json={
            'notrelated': 'to this api :(',
            'json': True
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'Error' in data
        assert data['Error'] == "Invalid friend_id"

        # Friendship doesn't exist between the users.
        response = self.client.post('/api/removefriend', json={
            'friend_id': 2,
            'json': True
        })
        assert response.status_code == 404
        data = response.get_json()
        assert 'Error' in data
        assert data['Error'] == "You are not friends with this user"

        # Friendship has not been accepted yet
        fq = Friendship(sender_id=self.user.id, recipient_id=2, status='pending', created_at=db.func.now())
        db.session.add(fq)
        db.session.commit()
        response = self.client.post('/api/removefriend', json={
            'friend_id': 2,
            'json': True
        })
        assert response.status_code == 404
        data = response.get_json()
        assert 'Error' in data
        assert data['Error'] == "You are not friends with this user"

        # Friendship was rejected
        fq.status = 'rejected'
        db.session.add(fq)
        db.session.commit()
        response = self.client.post('/api/removefriend', json={
            'friend_id': 2,
            'json': True
        })
        assert response.status_code == 404
        data = response.get_json()
        assert 'Error' in data
        assert data['Error'] == "You are not friends with this user"

        # Friendship exists & accepted
        fq.status = 'accepted'
        fq.accepted_at=db.func.now()
        db.session.add(fq)
        db.session.commit()
        response = self.client.post('/api/removefriend', json={
            'friend_id': 2,
            'json': True
        })
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert data['message'] == "Friend removed."

    # Hm..
    def test_friends_status(self):
        # Testing parameter not being sent
        response = self.client.get('/api/friendsstatus')
        assert response.status_code == 400
        data = response.get_json()
        assert "Error" in data
        assert data["Error"] == "Missing 'now' parameter"

        # Testing no friends (thus no status)
        response = self.client.get('/api/friendsstatus?now=2026-05-14T14:08:23.425')
        assert response.status_code == 200
        data = response.get_json()
        assert data == []

        # Testing with friends but they are free (No events exist under the friend)
        fq = Friendship(sender_id=self.user.id, recipient_id=2, status='accepted', created_at=db.func.now(), accepted_at=db.func.now())
        db.session.add(fq)
        db.session.commit()

        response = self.client.get('/api/friendsstatus?now=2026-05-14T14:08:23.425')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['email'] ==  'friend@fun.net'
        assert data[0]['id'] == 2
        assert data[0]['in_class'] == False
        assert data[0]['minutes_until_next'] == None
        assert data[0]['username'] == 'allen'

        # Friend has event in 30min.
        event = Event(
        title='name',
        date=date(2026, 5, 13),
        start_time=time(10, 0),
        end_time=time(11, 0),
        color='indigo',
        user_id=2

        )
        db.session.add(event)
        db.session.commit()

        response = self.client.get('/api/friendsstatus?now=2026-05-13T09:30:00.00')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['email'] ==  'friend@fun.net'
        assert data[0]['id'] == 2
        assert data[0]['in_class'] == False
        assert data[0]['minutes_until_next'] == 30
        assert data[0]['username'] == 'allen'

        # Friend is currently in an event that ends in 30 min
        response = self.client.get('/api/friendsstatus?now=2026-05-13T10:30:00.00')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['email'] ==  'friend@fun.net'
        assert data[0]['id'] == 2
        assert data[0]['in_class'] == True
        assert data[0]['minutes_until_next'] == -30
        assert data[0]['username'] == 'allen'

        # Testing multiple friends
        user = User(username="coolfriend", email="abcde@fg.com")
        db.session.add(user)
        fq = Friendship(sender_id=self.user.id, recipient_id=3, status='accepted', created_at=db.func.now(), accepted_at=db.func.now())
        db.session.add(fq)
        db.session.commit()

        response = self.client.get('/api/friendsstatus?now=2026-05-13T10:30:00.00')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2
        assert data[0]['email'] ==  'friend@fun.net'
        assert data[0]['id'] == 2
        assert data[0]['in_class'] == True
        assert data[0]['minutes_until_next'] == -30
        assert data[0]['username'] == 'allen'
        assert data[1]['email'] ==  "abcde@fg.com"
        assert data[1]['id'] == 3
        assert data[1]['in_class'] == False
        assert data[1]['minutes_until_next'] == None
        assert data[1]['username'] == 'coolfriend'

        return

    
