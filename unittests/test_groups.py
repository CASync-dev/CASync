import unittest
from app import create_app, db
from app.config import TestConfig
from app.models import Event, Friendship, User

class GroupTestCase(unittest.TestCase):
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

    # Referenced from test_friends
    def populate_db(self):
        # Create users
        main_user = User(username='gerald', email='sekai@hotmail.com') # userid = 1
        main_user.password = 'foo'

        friend1 = User(username='allen', email='friend@fun.net') # User to friend. id = 2
        friend1.password = 'bar'

        friend2 = User(username='bob', email='the@builder.com') # User to friend. id = 3
        friend2.password = 'ack'

        # Add users to database
        db.session.add(main_user)
        db.session.add(friend1)
        db.session.add(friend2)
        db.session.commit()

        # Making them be all be friends
        friendship1 = Friendship(user_id=main_user.id, friend_id=friend1.id, status='accepted', created_at=db.func.now())
        friendship2 = Friendship(user_id=main_user.id, friend_id=friend2.id, status='accepted', created_at=db.func.now())
        db.session.add(friendship1)
        db.session.add(friendship2)
        db.session.commit()

        # Simulates fake login session for the current user (gerald)
        with self.client.session_transaction() as session:
            session['_user_id'] = str(main_user.id)
            session['_fresh'] = True # for security-sensitive actions (Copied from Tehei's example)

        # Performs actual login request
        self.client.post('/login', data={'username': 'gerald', 'password': 'foo'})
        self.user = main_user

    
    def test_create_group(self):
        pass


    def test_group_friends_list(self):
        pass

    def test_add_group_member(self):
        pass

    def test_get_group(self):
        pass

    def test_leave_group(self):
        pass
    