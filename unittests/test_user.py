import unittest

from flask_login import login_user
from app import create_app, db
from app.config import TestConfig
from app.models import User

# TODO: Test other apis that use user.

# Tests User functionability: registering, logging, password hashing, apis, etc.
class UserTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestConfig())
        self.app.config['WTF_CSRF_ENABLED'] = False # Disables CSRF during tests
        self.app.config['LOGIN_DISABLED'] = True # Disable @login_required flags, so we can access the apis.
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        self.app = None
        self.app_context = None

    # Liam's test function from the old test branch/pr
    def test_user_creation(self):
        # Create a user and verify it was saved correctly
        user = User(username='testuser', email='test@example.com')
        db.session.add(user)
        db.session.commit()
        self.assertEqual(User.query.count(), 1)
        fetched = User.query.first()
        # Verify the fields were saved correctly
        self.assertEqual(fetched.username, 'testuser')
        self.assertEqual(fetched.email, 'test@example.com')
        self.assertIsNotNone(fetched.created_at)

    def test_password_hashing(self):
        u = User(username='greg', email='abcde@fghi.com')
        u.password = 'myawesomepass!'
        self.assertFalse(u.verify_password('notthepass!'))
        self.assertTrue(u.verify_password('myawesomepass!'))

    def test_gravatar(self):
        u = User(username='john', email='john@example.com')
        self.assertEqual(u.avatar(128), ('https://www.gravatar.com/avatar/d4c74594d841139328695756648b6bd6?d=identicon&s=128'))

    # How would we test actual avatars? System tests?

    def test_change_username(self):
        user = User(username='bot1', email='bottingmail@user.com')
        user.password = 'foobar'
        db.session.add(user)
        db.session.commit()
        with self.client.session_transaction() as session:
            session['_user_id'] = str(user.id)
            session['_fresh'] = True
        response = self.client.post('/api/changeusername', json={
            'newuser': 'bot',
        })
        assert response.status_code == 200
        assert response.json['success'] == 'bot'

        response = self.client.post('/api/changeusername', json={
            'newuser': 'gerald',
        })
        assert response.status_code == 200
        assert response.json['error'] == "Username already taken."

    def test_change_email(self):
        user = User(username='bot2', email='bottingbox@user.com')
        user2 = User(username='bot3', email="sekai@hotmail.com")
        db.session.add(user)
        db.session.add(user2)
        db.session.commit()
        user.password = 'foobar'

        with self.client.session_transaction() as session:
            session['_user_id'] = str(user.id)
            session['_fresh'] = True
        response = self.client.post('/api/changeemail', json={
            'newemailaddress': 'boxxingbot@user.com',
        })
        assert response.status_code == 200
        assert response.json['success'] == 'boxxingbot@user.com'

        response = self.client.post('/api/changeemail', json={
            'newemailaddress': 'sekai@hotmail.com',
        })
        assert response.status_code == 200
        assert response.json['error'] == 'Email already associated with another account.'

        response = self.client.post('/api/changeemail', json={
            'newemailaddress': 'notanemail',
        })
        assert response.status_code == 200
        assert response.json['error'] == 'Not an Email'

    def test_change_password(self):
        user = User(username='bot4', email="random@email.net")
        user.password = 'foobar'
        db.session.add(user)
        db.session.commit()
        # Testing on new password not being strong enough.
        # changePassform ="" tells the server that the data being sent is for that form.
        response = self.client.post("/settings", data = dict(current_password="foobar", new_password='badpass', repeat_new='badpass', changePassform=""), follow_redirects=True)
        assert response.status_code == 200
        assert response.request.path == '/settings'
        # The pass strength is already tested in test_reglog.py, so won't repeat it here.
        # Instead we'll just check the password has not been affected.
        assert user.verify_password('foobar') == True

        # Testing on not matching new passwords
        response = self.client.post("/settings", data = dict(current_password="foobar", new_password='P@ssw01d', repeat_new='d10wss@P', changePassform=""), follow_redirects=True)
        assert response.request.path == '/settings'
        html = response.get_data(as_text=True)
        assert 'Passwords must match' in html
        
        # Testing on current password being incorrect
        response = self.client.post("/settings", data = dict(current_password="barfoo", new_password='P@ssw01d', repeat_new='P@ssw01d', changePassform=""), follow_redirects=True)
        assert response.request.path == '/settings'
        html = response.get_data(as_text=True)
        assert "Error changing password: Incorrect password." in html

        # Testing if password change works
        response = self.client.post("/settings", data = dict(current_password="foobar", new_password='P@ssw01d', repeat_new='P@ssw01d', changePassform=""), follow_redirects=True)
        assert response.request.path == '/settings'
        html = response.get_data(as_text=True)
        assert "Successfully changed user's password." in html
        assert user.verify_password('P@ssw01d') == True

    def test_del_acc(self):
        user = User(username='testsubject', email= 'testing@yahoo.com')
        user.password = 'foobar'
        db.session.add(user)
        db.session.commit()
        # Testing incorrect email
        response = self.client.post('/settings', data = dict(email = 'myreal@mail.com', username= 'testsubject', password='foobar', acdform=""), follow_redirects=True)
        assert response.request.path == '/settings'
        html = response.get_data(as_text=True)
        assert 'Error in account deletion: Incorrect email.' in html
        
        # Testing incorrect username
        response = self.client.post('/settings', data = dict(email = 'testing@yahoo.com', username= 'fakeuser', password='foobar', acdform=""), follow_redirects=True)
        assert response.request.path == '/settings'
        html = response.get_data(as_text=True)
        assert 'Error in account deletion: Incorrect username.' in html

        # Testing incorrect password
        response = self.client.post('/settings', data = dict(email = 'testing@yahoo.com', username= 'testsubject', password='barfoo', acdform=""), follow_redirects=True)
        assert response.request.path == '/settings'
        html = response.get_data(as_text=True)
        assert 'Error in account deletion: Incorrect password.' in html

        # Testing actual deletion
        response = self.client.post('/settings', data = dict(email = 'testing@yahoo.com', username= 'testsubject', password='foobar', acdform=""), follow_redirects=True)
        assert response.request.path == '/login'
        html = response.get_data(as_text=True)
        assert 'Your account has been deleted.' in html
        user = User.query.filter_by(username='testsubject').first()
        assert user == False

        
    # iCal Link imports to be handled by test_ical.py.

        
        


