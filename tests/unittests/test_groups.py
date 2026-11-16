import unittest
from app import create_app, db
from app.config import TestConfig
from app.models import Friendship, User, Group

# Command to run all test case/class (fast copy paste):
# python -m unittest -v tests.unittests.test_groups

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

    # Referenced from test_friends (minimal and reusable, other tests may add to this)
    def populate_db(self):
        # Create users
        # These seeded users log in via the /login route, so they're confirmed.
        self.main_user = User(username='gerald', email='sekai@hotmail.com') # id = 1
        self.main_user.password = 'foo'
        self.main_user.email_confirmed = True

        self.friend1 = User(username='allen', email='friend@fun.net') # User to friend. id = 2
        self.friend1.password = 'bar'
        self.friend1.email_confirmed = True

        self.friend2 = User(username='bob', email='the@builder.com') # User to friend. id = 3
        self.friend2.password = 'ack'
        self.friend2.email_confirmed = True

        self.non_friend = User(username='rick', email='nevergonnagive@youup.com') # User to not friend, id = 4
        self.non_friend.password = 'roll'
        self.non_friend.email_confirmed = True

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

        self.login_user(self.main_user, "foo")

    # Helper functions
    def login_user(self, user, password):
        # Ensure that whoever was logged in previous is logged out
        self.logout_user()

        # Simulates (manually) fake login session for the current user (gerald)
        # with self.client.session_transaction() as session:
        #     session['_user_id'] = str(user.id)
        #     session['_fresh'] = True # for security-sensitive actions (Copied from Tehei's example)

        # Performs actual login request
        self.client.post('/login', data={
            'username': user.username, 
            'password': password
        })
        self.main_user = user

    def logout_user(self):
        # Simulated log out
        # with self.client.session_transaction() as session:
        #     session.clear()

        # Actual logout
        self.client.get("/logout")

    def create_group(self, name, members):
        return self.client.post('/api/group/create', json={
            "name": name,
            "list": members # sends list of friends, current user manually added in the api
        })

    # ------------------------------------------------------------------------------ #

# Command to run this test case/class (fast copy paste):
# python -m unittest -v tests.unittests.test_groups.GroupCreationTestCase
class GroupCreationTestCase(BaseTestCase):
    # Testing Group Creation 

    # -- Testing creation of group with current user's friends -- #
    def test_create_group_success(self):
        response = self.create_group(
            "Study (Till You) Break",
            [self.friend1.username, self.friend2.username] # sends list of friends, current user manually added in the api
        )

        # Verifies response is successful
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["group"]["group_name"], "Study (Till You) Break")

        # Verifies database insert is also successful
        group = Group.query.filter_by(group_name="Study (Till You) Break").first()
        self.assertIsNotNone(group)

        # Verify all API response members in the group
        member_names_api = [member["username"] for member in data["group"]["members"]]
        self.assertCountEqual(member_names_api, [self.main_user.username, self.friend1.username, self.friend2.username])

        # Verify all database members in the group 
        member_names_db = [member.username for member in group.members]
        self.assertCountEqual(member_names_db, [self.main_user.username, self.friend1.username, self.friend2.username])

    # -- Testing creation of group with users who are not friends with current user -- #
    def test_create_group_non_friend(self):
        response = self.create_group(
            "Who are You?",
            [self.friend1.username, self.non_friend.username]
        )

        # Verifies response should fail (you should not be able to add non friends)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"] )
        self.assertIn("error", data)
        self.assertEqual(
            data["error"],
            f"User {self.non_friend.username} is not your friend"
        )

    # -- Testing creation of group with users who do not exist in the system -- #
    def test_create_group_nonexistent_user(self):
        nonexistent_username = "sus"

        response = self.create_group(
            "No Seriously, Who are You?",
            [self.friend1.username, nonexistent_username]
        )

        # Verifies response should fail (you should not be able to add nonexistent user)
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertIn("error", data)
        self.assertEqual(
            data["error"],
            f"User {nonexistent_username} not found"
        )

    # -- Testing creation of group with no group name given -- #
    def test_create_group_missing_name(self):
        response = self.create_group(
            "",
            [self.friend1.username, self.friend2.username]
        )

        # Verifies response should fail (group name is required)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertIn("error", data)
        self.assertEqual(
            data["error"],
            "Group name required"
        )

    # -- Testing creation of group with no friends selected -- #
    def test_create_group_empty_list(self):
        group_name = "Wow, so many friends"
        response = self.create_group(
            group_name,
            []
        )

        # Verifies successful response (can make group with only current user)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertTrue(data["success"] )
        self.assertEqual(data["group"]["group_name"], group_name)

        # Verifies database insert is also successful
        group = Group.query.filter_by(group_name=group_name).first()
        self.assertIsNotNone(group)

        # Verifies only current user in the group (API response)
        member_names_api = [member["username"] for member in data["group"]["members"]]
        self.assertCountEqual(member_names_api, [self.main_user.username])

        # Verifies only current user in the group (database)
        member_names_db = [member.username for member in group.members]
        self.assertCountEqual(member_names_db, [self.main_user.username])

# Command to run this test case/class (fast copy paste):
# python -m unittest -v tests.unittests.test_groups.GroupMembershipTestCase
class GroupMembershipTestCase(BaseTestCase):
    # -- Testing getting current user's friends -- #
    def test_group_get_friends_list(self):
        response = self.client.get("/api/group/friends")

        # Verifies response is successful and contains friends
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIn("friends", data)
        self.assertEqual(len(data["friends"]), 2)

        # Validate actual usernames
        friend_names = [friend["username"] for friend in data["friends"]]
        self.assertIn(self.friend1.username, friend_names)
        self.assertIn(self.friend2.username, friend_names)

        # Validate non-friends not included in list
        self.assertNotIn(self.non_friend.username, friend_names)

    # ------------------------------------------------------------------------------ #

    # -- Testing getting group details -- #
    def test_get_group_details(self):
        # Create group
        group_name = "Hello Group!"
        response_group = self.create_group(
            group_name,
            [self.friend1.username, self.friend2.username]
        )
        self.assertEqual(response_group.status_code, 201)

        # Get data from response
        data_group = response_group.get_json()
        group_id = data_group["group"]["id"]

        # Call the GET endpoint
        response_details = self.client.get(f"/api/group/{group_id}")
        self.assertEqual(response_details.status_code, 200)

        data_details = response_details.get_json()
        self.assertEqual(data_details["group_name"], group_name)

        # Verify members retrieved correctly
        member_names = [member["username"] for member in data_details["members"]]
        self.assertCountEqual(member_names, [self.main_user.username, self.friend1.username, self.friend2.username])

    def test_get_nonexistent_group_details(self):
        nonexistent_id = 999
        response = self.client.get(f"/api/group/{nonexistent_id}")

        self.assertEqual(response.status_code, 404)

        data = response.get_json()
        self.assertEqual(data["error"], "Could not find group")
    # ------------------------------------------------------------------------------ #

    # -- Testing adding a new member to existing group -- #
    def test_add_group_member_success(self):
        # Create group
        group_name = "Another One!"
        response_group = self.create_group(
            group_name,
            [self.friend1.username]
        )
        self.assertEqual(response_group.status_code, 201)

        # Get data from response
        data_group = response_group.get_json()
        group_id = data_group["group"]["id"]
        friends_to_add = [self.friend2.username]

        # Call the add member method
        response = self.client.post("/api/group/add_member", json = {
            "group_id": group_id,
            "list": friends_to_add
        })

        self.assertEqual(response.status_code, 200)

        # Verify the response has correctly added the user
        data = response.get_json()
        friends_names = [added_user["username"] for added_user in data["added_users"]]

        self.assertTrue(data["success"])
        self.assertIn(self.friend2.username, friends_names)

        # Database check the added user
        group = db.session.get(Group, group_id)
        self.assertIn(self.friend2, group.members)
    
    # -- Testing adding a user who does not exist to existing group -- #
    def test_add_nonexistent_member(self):
        # Create group
        group_name = "Another One!"
        response_group = self.create_group(
            group_name,
            [self.friend1.username]
        )
        self.assertEqual(response_group.status_code, 201)

        # Get data from response
        data_group = response_group.get_json()
        group_id = data_group["group"]["id"]
        nonexistent_user = "whomst"
        friends_to_add = [nonexistent_user]

        # Call the add member method
        response = self.client.post("/api/group/add_member", json = {
            "group_id": group_id,
            "list": friends_to_add
        })

        data = response.get_json()

        # Verify response should not be successful (cannot add user who doesn't exist)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data["success"])
        self.assertIn("not_found", data)
        self.assertIn(nonexistent_user, data["not_found"])
        self.assertEqual(
            data["error"], 
            "No valid users were added. User(s) may already be in the group or does not exist."
        )

    # -- Testing adding a user who does already exists in the group -- #
    def test_add_member_already_in_group(self):
        # Create group
        group_name = "You're already here, buddy!"
        response_group = self.create_group(
            group_name,
            [self.friend1.username, self.friend2.username]
        )
        self.assertEqual(response_group.status_code, 201)

        # Get data from response
        data_group = response_group.get_json()
        group_id = data_group["group"]["id"]
        friends_to_add = [self.friend1.username]

        # Call the add member method
        response = self.client.post("/api/group/add_member", json = {
            "group_id": group_id,
            "list": friends_to_add
        })

        data = response.get_json()

        # Verify response should not be successful (cannot add user who's already in the group)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data["success"])
        self.assertIn("skipped", data)
        self.assertIn(self.friend1.username, data["skipped"])
        self.assertEqual(
            data["error"], 
            "No valid users were added. User(s) may already be in the group or does not exist."
        )

    # -- Testing adding a users who either already existed in group, new user actually added, and nonexistent user -- #
    def test_add_member_mixed_input(self):
        # Create group
        group_name = "Study :("
        response_group = self.create_group(
            group_name,
            [self.friend1.username]
        )
        self.assertEqual(response_group.status_code, 201)

        # Get data from response
        data_group = response_group.get_json()
        nonexistent_user = "ghost"
        group_id = data_group["group"]["id"]
        friends_to_add = [self.friend1.username, self.friend2.username, nonexistent_user]

        # Call the add member method
        response = self.client.post("/api/group/add_member", json = {
            "group_id": group_id,
            "list": friends_to_add
        })

        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertIn(self.friend2.username, [user["username"] for user in data["added_users"]])
        self.assertIn(nonexistent_user, data["not_found"])
        self.assertIn(self.friend1.username, data["skipped"])
        self.assertEqual(data["message"], "Added 1 member(s) to group")

    # -- Testing adding a user but missing id was given -- #
    def test_add_member_missing_group_id(self):
        friends_to_add = [self.friend1.username, self.friend2.username]

        # Call the add member method
        response = self.client.post("/api/group/add_member", json = {
            "list": friends_to_add
        })

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "group_id is required")

    # -- Testing adding a user but no isers were given -- #
    def test_add_member_empty_list(self):
        # Create group
        group_name = "Study :("
        response_group = self.create_group(
            group_name,
            [self.friend1.username]
        )
        self.assertEqual(response_group.status_code, 201)

        # Get data from response
        data_group = response_group.get_json()
        group_id = data_group["group"]["id"]

        # Call the add member method
        response = self.client.post("/api/group/add_member", json = {
            "group_id": group_id,
            "list": []
        })

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "No users to add")

    # -- Testing adding a user but the person adding is not in the group (not authenticated/allowed) -- #
    def test_add_member_adder_not_in_group(self):
        # Create group
        group_name = "Study :("
        response_group = self.create_group(
            group_name,
            [self.friend1.username]
        )
        self.assertEqual(response_group.status_code, 201)

        # Get data from response
        data_group = response_group.get_json()
        group_id = data_group["group"]["id"]

        # Login as a different user not friends with anyone in group
        self.logout_user()
        self.login_user(self.non_friend, "roll")

        # Call the add member method
        response = self.client.post("/api/group/add_member", json = {
            "group_id": group_id,
            "list": [self.friend2.username]
        })

        self.assertEqual(response.status_code, 403)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "You are not in this group")


    # ------------------------------------------------------------------------------ #

    def test_leave_group_success(self):
        # Create group
        group_name = "Study :("
        response_group = self.create_group(
            group_name,
            [self.friend1.username, self.friend2.username]
        )
        self.assertEqual(response_group.status_code, 201)

        # Get data from response
        data_group = response_group.get_json()
        group_id = data_group["group"]["id"]

        response = self.client.post("/api/group/leave", json = {
            "group_id": group_id,
        })

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "You have successfully left the group.")

        # Check the database to see member has indeed left
        group = Group.query.filter_by(group_name=group_name).first()
        self.assertIsNotNone(group)
        self.assertNotIn(self.main_user.username, [member.username for member in group.members])


    def test_leave_group_no_remaining_members(self):
        # Create group
        group_name = "Study :("
        response_group = self.create_group(
            group_name,
            []
        )
        self.assertEqual(response_group.status_code, 201)

        # Get data from response
        data_group = response_group.get_json()
        group_id = data_group["group"]["id"]

        response = self.client.post("/api/group/leave", json = {
            "group_id": group_id,
        })

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "You have successfully left the group.")

        # Check that group does not exist in the db anymore
        group = Group.query.filter_by(group_name=group_name).first()
        self.assertIsNone(group)

    def test_leave_group_member_not_in_group(self):
        # Create group
        group_name = "Study :("
        response_group = self.create_group(
            group_name,
            [self.friend1.username]
        )
        self.assertEqual(response_group.status_code, 201)

        # Get data from response
        data_group = response_group.get_json()
        group_id = data_group["group"]["id"]

        self.logout_user()
        self.login_user(self.friend2, "ack")

        response = self.client.post("/api/group/leave", json = {
            "group_id": group_id,
        })

        self.assertEqual(response.status_code, 403)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "You are not in this group")

    def test_leave_group_invalid_group(self):
        nonexistent_group_id = 999
        response = self.client.post("/api/group/leave", json = {
            "group_id": nonexistent_group_id,
        })

        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "Group not found")

    def test_leave_group_invalid_id(self):
        response = self.client.post("/api/group/leave", json = {
            "group_id": "nope",
        })

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "Invalid group_id")
    # ------------------------------------------------------------------------------ #
