import unittest
from app import create_app, db
from app.config import TestConfig
from app.models import Event, Friendship, User, Group

# Command to run this test case/class (fast copy paste):
# python -m unittest -v unittests.test_groups.GroupCreationTestCase
class BaseTestCase(unittest.TestCase):
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
        # closes all SQLite connections (added due to ResourceWarning: unclosed database...)
        db.engine.dispose()
        self.app_context.pop()
        self.app = None
        self.app_context = None

    # Referenced from test_friends
    def populate_db(self):
        # Create users
        self.main_user = User(username='gerald', email='sekai@hotmail.com') # id = 1
        self.main_user.password = 'foo'

        self.friend1 = User(username='allen', email='friend@fun.net') # User to friend. id = 2
        self.friend1.password = 'bar'

        self.friend2 = User(username='bob', email='the@builder.com') # User to friend. id = 3
        self.friend2.password = 'ack'

        self.non_friend = User(username='rick', email='nevergonnagive@youup.com') # User to not friend, id = 4
        self.non_friend.password = 'roll'

        # Add users to database
        db.session.add_all([
            self.main_user,
            self.friend1,
            self.friend2,
            self.non_friend
        ])

        db.session.commit()

        # Create friendships
        friends = [self.friend1, self.friend2] # implemented as loop for scalability if want to test more friends
        for friend in friends:
            friendship = Friendship(sender_id=self.main_user.id, recipient_id=friend.id, status='accepted', created_at=db.func.now())
            db.session.add(friendship)
        db.session.commit()

        self.login_user(self.main_user)

    def login_user(self, user):
        # Simulates (manually) fake login session for the current user (gerald)
        with self.client.session_transaction() as session:
            session['_user_id'] = str(user.id)
            session['_fresh'] = True # for security-sensitive actions (Copied from Tehei's example)

        # Performs actual login request
        # self.client.post('/login', data={'username': 'gerald', 'password': 'foo'})
        # self.main_user = main_user

    def create_group(self, name, members):
        return self.client.post('/api/group/create', json={
            "name": name,
            "list": members # sends list of friends, current user manually added in the api
        })

    # ------------------------------------------------------------------------------ #

class GroupCreationTestCase(BaseTestCase):
    # Testing Group Creation 

    # -- Testing creation of group with current user's friends -- #
    def test_create_group_success(self):
        response = self.create_group(
            "Study (Till You) Break",
            ["allen", "bob"] # sends list of friends, current user manually added in the api
        )

        # Verifies response is successful
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertTrue(data["success"] )
        self.assertEqual(data["group"]["group_name"], "Study (Till You) Break")

        # Verifies database insert is also successful
        group = Group.query.filter_by(group_name="Study (Till You) Break").first()
        self.assertIsNotNone(group)

        # Verify all API response members in the group
        member_names_api = [member["username"] for member in data["group"]["members"]]
        self.assertCountEqual(member_names_api, ["allen", "gerald", "bob"])

        # Verify all database members in the group 
        member_names_db = [member.username for member in group.members]
        self.assertCountEqual(member_names_db, ["allen", "gerald", "bob"])

    # -- Testing creation of group with users who are not friends with current user -- #
    def test_create_group_non_friend(self):
        pass

    def test_create_group_nonexistent_user(self):
        pass

    def test_create_group_missing_name(self):
        pass

    def test_create_group_empty_list(self):
        pass


class GroupManagementTestCase(BaseTestCase):
    def test_group_friends_list(self):
        pass

    # ------------------------------------------------------------------------------ #

    def test_add_group_member(self):
        pass

    # ------------------------------------------------------------------------------ #

    def test_get_group(self):
        pass
    
    # ------------------------------------------------------------------------------ #

    def test_leave_group(self):
        pass
    
    # ------------------------------------------------------------------------------ #
