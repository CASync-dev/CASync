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
        with self.client.session_transaction() as session:
            session['_user_id'] = str(user.id)
            session['_fresh'] = True # Copied from Tehei's example.

    def test_getuser(self):
        # Test wrong data being submitted to the api
        response = self.client.post('/api/getusers', json={
            'username': 'bob'
        }, follow_redirects=True)
        assert response.status_code == 400
        assert response == {"Error: Invalid search"}
        
        # Test no data associated with 'search'
        response = self.client.post('/api/getusers', json={
            'search': ""
        })
        assert response.status_code == 400
        assert response == {"Error: Invalid search"}

        # Test email; Does not exist
        response = self.client.post('/api/getusers', json={
            'search': "fakeemail@mail.com"
        })
        assert response.status_code == 200
        assert response['results'] == 0

        # Test email; Is current users
        response = self.client.post('/api/getusers', json={
            'search': 'sekai@hotmail.com'
        })
        assert response.status_code == 200
        assert response['results'] == 0

        # Test email; User exists

        response = self.client.post('/api/getusers', json={
            'search': 'friend@fun.net'
        })
        assert response.status_code == 200
        assert response['results'] == { 2: 'allen'} # Don't know if this is the right format, check prior to merge

        # Test Username; user does not exist
        response = self.client.post('/api/getusers', json={
            'search': 'fakeuser'
        })
        assert response.status_code == 200
        assert response['results'] == 0

        # Test username; Is current users
        response = self.client.post('/api/getusers', json={
            'search': 'gerald'
        })
        assert response.status_code == 200
        assert response['results'] == 0

        # Test Username; User exists
        response = self.client.post('/api/getusers', json={
            'search': 'allen'
        })
        assert response.status_code == 200
        assert response['results'] == { 2: 'allen'}

        # Request has already been made and shouldn't show up
        f = Friendship(sender_id=current_user.id, recipient_id=2, status='pending', created_at=db.func.now())
        db.session.add(f)
        db.session.commit()

        # Testing searching when a request has already been made (Email)--------------------------
        response = self.client.post('/api/getusers', json={
            'search': 'friend@fun.net'
        })
        assert response.status_code == 200
        assert response['results'] == 0

        # User
        response = self.client.post('/api/getusers', json={
            'search': 'allen'
        })
        assert response.status_code == 200
        assert response['results'] == 0
        # ----------------------------------------------------------------------------------------
        # Testing searching when request rejected.
        f.status = 'rejected'
        response = self.client.post('/api/getusers', json={
            'search': 'friend@fun.net'
        })
        assert response.status_code == 200
        assert response['results'] == { 2: 'allen'}

        response = self.client.post('/api/getusers', json={
            'search': 'allen'
        })
        assert response.status_code == 200
        assert response['results'] == { 2: 'allen'}

        # Testing searching when request accepted.
        f.status = 'accepted'
        f.accepted_at = db.func.now()
        response = self.client.post('/api/getusers', json={
            'search': 'friend@fun.net'
        })
        assert response.status_code == 200
        assert response['results'] == 0

        # User
        response = self.client.post('/api/getusers', json={
            'search': 'allen'
        })
        assert response.status_code == 200
        assert response['results'] == 0

    def test_requestfriend(self):
        # Wrong data sent to api
        response = self.client.post('/api/requestfriend', json={
            'wrongdata': 'whatspopping'
        })
        assert response.status_code == 400
        assert response == {"Error: Invalid user_id"}

        # User does not exist (Just in case somehow the webpage sends a non-existent user id)
        response = self.client.post('/api/requestfriend', json={
            'user_id': '50'
        })
        assert response.status_code == 404
        assert response == {"Error: User not found"}

        # User exists and no existing friend request exists between them.
        response = self.client.post('/api/requestfriend', json={
            'user_id': '2'
        })
        assert response.status_code == 200
        assert response['message'] == "Friend request sent to allen!"

        # User exists, and an existing friend request already exists
        response = self.client.post('/api/requestfriend', json={
            'user_id': '2'
        })
        assert response.status_code == 400
        assert response['error'] == "Friend request already pending"

        # User was rejected
        fq = Friendship.query.filter(Friendship.recipient_id == 2).first()
        fq.status = 'rejected'
        db.session.commit(fq)
        response = self.client.post('/api/requestfriend', json={
            'user_id': '2'
        })
        assert response.status_code == 200
        assert response['message'] == "Friend request sent to allen!"

        # User is already friends
        fq.status = 'accepted'
        fq.accepted_at = db.func.now()
        db.session.commit(fq)
        response = self.client.post('/api/requestfriend', json={
            'user_id': '2'
        })
        assert response.status_code == 400
        assert response['error'] == "You are already friends"
        
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
        response = self.client.post('/api/acceptfriend', json={
            'notrelated': 'to this api :('
        })
        assert response.status_code == 400
        assert response == {"Error: Invalid request_id"}

        # Testing request does not exist
        response = self.client.post('/api/acceptfriend', json={
            'request_id': 105
        })
        assert response.status_code == 404
        assert response == {"Error: No pending friend request found"}

        # Testing request does not belong to us
        notourid = not_our_request.id
        response = self.client.post('/api/acceptfriend', json={
            'request_id': notourid
        })
        assert response.status_code == 403
        assert response == {"Error: You can only accept friend requests sent to you"}

        # Testing accept request (actuals)
        realfriendshipid = new_request.id
        response = self.client.post('/api/acceptfriend', json={
            'request_id': realfriendshipid
        })
        assert response.status_code == 200
        assert response['message'] == "Friend request accepted from allen!"
        assert Friendship.query.filter(Friendship.id == request_id).first.status == 'accepted'

        # Testing request already accepted! So should not show up again.
        response = self.client.post('/api/acceptfriend', json={
            'request_id': realfriendshipid
        })
        assert response.status_code == 404
        assert response == {"Error: No pending friend request found"}


    def test_rejectfriend(self):
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

        # Test required field not in json
        response = self.client.post('/api/rejectfriend', json={
            'notrelated': 'to this api :('
        })
        assert response.status_code == 400
        assert response == {"Error: Invalid request_id"}

        # Testing request does not exist
        response = self.client.post('/api/rejectfriend', json={
            'request_id': 105
        })
        assert response.status_code == 404
        assert response == {"Error: No pending friend request found"}

        # Testing rejecting a request where the current user is not the recipient
        notourid = not_our_request.id
        response = self.client.post('/api/rejectfriend', json={
            'request_id': notourid
        })
        assert response.status_code == 403
        assert response == {"Error: You can only reject friend requests sent to you"}

        # Testing actuals
        realfriendshipid = new_request.id
        response = self.client.post('/api/rejectfriend', json={
            'request_id': realfriendshipid
        })
        assert response.status_code == 200
        assert response['message'] == "Friend request rejected."

        # Request rejected already, so can't reject again
        response = self.client.post('/api/rejectfriend', json={
            'request_id': realfriendshipid
        })
        assert response.status_code == 404
        assert response == {"Error: No pending friend request found"}

    def test_removefriend(self):
        # Test required field not in json
        response = self.client.post('/api/removefriend', json={
            'notrelated': 'to this api :('
        })
        assert response.status_code == 400
        assert response == {"Error: Invalid friend_id"}

        # Friendship doesn't exist between the users.
        response = self.client.post('/api/removefriend', json={
            'friend_id': 2
        })
        assert response.status_code == 404
        assert response == {"Error: You are not friends with this user"}

        # Friendship has not been accepted yet
        fq = Friendship(sender_id=current_user.id, recipient_id=2, status='pending', created_at=db.func.now(), accepted_at=db.func.now())
        db.session.add(fq)
        db.session.commit()
        response = self.client.post('/api/removefriend', json={
            'friend_id': 2
        })
        assert response.status_code == 404
        assert response == {"Error: You are not friends with this user"}

        # Friendship was rejected
        fq.status = 'rejected'
        db.session.add(fq)
        db.session.commit()
        response = self.client.post('/api/removefriend', json={
            'friend_id': 2
        })
        assert response.status_code == 404
        assert response == {"Error: You are not friends with this user"}

        # Friendship exists & accepted
        fq.status = 'accepted'
        db.session.add(fq)
        db.session.commit()
        response = self.client.post('/api/removefriend', json={
            'friend_id': 2
        })
        assert response.status_code == 200
        assert response['message'] == "Friend removed."

    # Hm..
    def test_friends_status(self):
        response = self.client.post('/api/friendsstatus', json={
            'notrelated': 'to this api :('
        })
        assert response.status_code == 400
        assert response == {"Error: Invalid friend_id"}

    
