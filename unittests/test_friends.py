import unittest

from flask_login import current_user, login_user
from app import create_app, db
from app.config import TestConfig
from app.models import Friendship, User

class FriendsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestConfig())
        self.app.config['WTF_CSRF_ENABLED'] = False # Disables CSRF during tests
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.populate_db()
        self.client = self.app.test_client()

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
        login_user(user) # Is this the right way to login as a user..?

    def test_getuser(self):
        # Test wrong data being submitted to the api
        response = self.client.post('/api/getusers', data={
            'username': 'bob'
        }, follow_redirects=True)
        assert response.status_code == 400
        assert response == {"Error: Invalid search"}
        
        # Test no data associated with 'search'
        response = self.client.post('/api/getusers', data={
            'search': ""
        })
        assert response.status_code == 400
        assert response == {"Error: Invalid search"}

        # Test email; Does not exist
        response = self.client.post('/api/getusers', data={
            'search': "fakeemail@mail.com"
        })
        assert response.status_code == 200
        assert response['results'] == 0

        # Test email; Is current users
        response = self.client.post('/api/getusers', data={
            'search': 'sekai@hotmail.com'
        })
        assert response.status_code == 200
        assert response['results'] == 0

        # Test email; User exists

        response = self.client.post('/api/getusers', data={
            'search': 'friend@fun.net'
        })
        assert response.status_code == 200
        assert response['results'] == { 2: 'allen'} # Don't know if this is the right format, check prior to merge

        # Test Username; user does not exist
        response = self.client.post('/api/getusers', data={
            'search': 'fakeuser'
        })
        assert response.status_code == 200
        assert response['results'] == 0

        # Test username; Is current users
        response = self.client.post('/api/getusers', data={
            'search': 'gerald'
        })
        assert response.status_code == 200
        assert response['results'] == 0

        # Test Username; User exists
        response = self.client.post('/api/getusers', data={
            'search': 'allen'
        })
        assert response.status_code == 200
        assert response['results'] == 0

    def test_requestfriend(self):
        # Wrong data sent to api
        response = self.client.post('/api/requestfriend', data={
            'wrongdata': 'whatspopping'
        })
        assert response.status_code == 400
        assert response == {"Error: Invalid user_id"}

        # User does not exist (Just in case somehow the webpage sends a non-existent user id)
        response = self.client.post('/api/requestfriend', data={
            'user_id': '50'
        })
        assert response.status_code == 404
        assert response == {"Error: User not found"}

        # User exists and no existing friend request exists between them.
        response = self.client.post('/api/requestfriend', data={
            'user_id': '2'
        })
        assert response.status_code == 200
        assert response['message'] == "Friend request sent to allen!"

        # User exists, and an existing friend request already exists
        response = self.client.post('/api/requestfriend', data={
            'user_id': '2'
        })
        assert response.status_code == 400
        assert response['error'] == "Friend request already pending"

        # Should really test making req on a uesr who's already friends, but might be easier to do that in test_acceptfriend()
        
        # Testing searching when a request has already been made (Email)--------------------------
        response = self.client.post('/api/getusers', data={
            'search': 'friend@fun.net'
        })
        assert response.status_code == 200
        assert response['results'] == 0

        # User
        response = self.client.post('/api/getusers', data={
            'search': 'allen'
        })
        assert response.status_code == 200
        assert response['results'] == 0
        # ----------------------------------------------------------------------------------------


    def test_acceptfriend(self):
        # Creating the friendship explicitly incase previous test did not work. Probably not a good idea to rely on
        # Other apis for isolated tests :)
        new_request = Friendship(sender_id=2, recipient_id=current_user.id, status='pending', created_at=db.func.now()) # so that sender is our 'friend' user
        user = User(username="coolnotfriend", email="abcde@fg.com")
        user.password = 'foobar' # Not required but why not :')
        db.session.add(user)
        not_our_request = Friendship(sender_id=user.id, recipient_id=2, status='pending', created_at=db.func.now()) # Request that the current user did not send and not for.
        db.session.add(new_request)
        db.session.add(not_our_request)
        db.session.commit()

        request_id = new_request.id
        # Testing not valid id submitted
        response = self.client.post('/api/acceptfriend', data={
            'notrelated': 'to this api :('
        })
        assert response.status_code == 400
        assert response == {"Error: Invalid request_id"}

        # Testing request does not exist
        response = self.client.post('/api/acceptfriend', data={
            'request_id': '105'
        })
        assert response.status_code == 404
        assert response == {"Error: No pending friend request found"}

        # Testing request does not belong to us
        

        # Testing accept request (actuals)




    def test_rejectfriend(self):
        print()

    def test_removefriend(self):
        print()

    def test_friends_status(self):
        print()

    
