import unittest
from app import create_app, db
from flask import current_app
from app.config import TestConfig
from app.models import User
# Do tests on this non-persistent database

# Tests registration and logging in
class RegLogTestCase(unittest.TestCase):
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

        # closes all SQLite connections (added due to ResourceWarning: unclosed database...)
        db.engine.dispose()

        self.app_context.pop()
        self.app = None
        self.app_context = None

    def populate_db(self):
        user = User(username='gerald', email='sekai@hotmail.com')
        user.password = 'foo'
        db.session.add(user)
        db.session.commit()

    def test_app(self):
        assert self.app is not None
        assert current_app == self.app

    def test_registration_form(self):
        response = self.client.get('/register')
        assert response.status_code == 200
        html = response.get_data(as_text=True)

        # Make sure required fields are generated
        assert 'name="email"' in html
        assert 'name="username"' in html
        assert 'name="password"' in html
        assert 'name="repeat_password"' in html
        assert 'name="rme"' in html
        assert 'id="log"' in html # submit button doesn't have a name..?

    def test_login_form(self):
        response = self.client.get('/login')
        assert response.status_code == 200
        html = response.get_data(as_text=True)

        assert 'name="username"' in html
        assert 'name="password"' in html
        assert 'name="rme"' in html
        assert 'id="log"' in html # submit button doesn't have a name..?

    def test_register_user(self):
        response = self.client.post('/register', data={
            'username': 'bob',
            'email': 'bob12345@testing.com',
            'password': 'P@ssw01d',
            'repeat_password': 'P@ssw01d',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert response.request.path == '/dash'
        # Should be at /dash right now. We want to test if the account was actually created, 
        # We'll log out and login with the same user.
        response = self.client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        assert response.request.path == '/login'
        # Login with new user
        response = self.client.post('/login', data={
            'username': 'bob',
            'password': 'P@ssw01d'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert response.request.path == '/dash'
        html = response.get_data(as_text=True)
        # Check if current user logged in is our user:
        assert 'bob' in html

    # ------ Form Validation ----------------
    def test_register_unique_email(self):
        response = self.client.post('/register', data={
            'username': 'bobby',
            'email': 'sekai@hotmail.com',
            'password': 'P@ssw01d',
            'repeat_password': 'P@ssw01d',
        })
        assert response.status_code == 200
        assert response.request.path == '/register'
        html = response.get_data(as_text=True)
        assert 'Email already registered.' in html

    def test_register_unique_username(self):
        response = self.client.post('/register', data={
            'username': 'gerald',
            'email': 'randomUni@uni.edu.au',
            'password': 'P@ssw01d',
            'repeat_password': 'P@ssw01d',
        })
        assert response.status_code == 200
        assert response.request.path == '/register'
        html = response.get_data(as_text=True)
        assert 'Username already taken.' in html

    def test_register_mismatch_password(self):
        response = self.client.post('/register', data={
            'username': 'bobby',
            'email': 'randomUni@uni.edu.au',
            'password': 'P@ssw01d',
            'repeat_password': 'd10wss@P',
        })
        assert response.status_code == 200
        assert response.request.path == '/register'
        html = response.get_data(as_text=True)
        assert 'Passwords must match' in html

    def test_register_pass_strength(self):
        # Very weak pass, no requirements met
        response = self.client.post('/register', data={
            'username': 'bobby',
            'email': 'randomUni@uni.edu.au',
            'password': 'e',
            'repeat_password': 'e',
        })
        assert response.status_code == 200
        assert response.request.path == '/register'
        html = response.get_data(as_text=True)
        assert 'Password must contain: at least 8 characters, one uppercase letter, one number, one special character.' in html

        # Similarly...:
        response = self.client.post('/register', data={
            'username': 'bobby',
            'email': 'randomUni@uni.edu.au',
            'password': 'eE',
            'repeat_password': 'eE',
        })
        assert response.status_code == 200
        assert response.request.path == '/register'
        html = response.get_data(as_text=True)
        assert 'Password must contain: at least 8 characters, one number, one special character.' in html

        # No special char:
        response = self.client.post('/register', data={
            'username': 'bobby',
            'email': 'randomUni@uni.edu.au',
            'password': 'eE1',
            'repeat_password': 'eE1',
        })
        assert response.status_code == 200
        assert response.request.path == '/register'
        html = response.get_data(as_text=True)
        assert 'Password must contain: at least 8 characters, one special character.' in html

        # All but password length:
        response = self.client.post('/register', data={
            'username': 'bobby',
            'email': 'randomUni@uni.edu.au',
            'password': 'eE1!',
            'repeat_password': 'eE1!',
        })
        assert response.status_code == 200
        assert response.request.path == '/register'
        html = response.get_data(as_text=True)
        assert 'Password must contain: at least 8 characters.' in html

        response = self.client.post('/register', data={
            'username': 'bobby',
            'email': 'randomUni@uni.edu.au',
            'password': 'eeeeeeeee1!',
            'repeat_password': 'eeeeeeeee1!',
        })
        assert response.status_code == 200
        assert response.request.path == '/register'
        html = response.get_data(as_text=True)
        assert 'Password must contain: one uppercase letter.' in html

        response = self.client.post('/register', data={
            'username': 'bobby',
            'email': 'randomUni@uni.edu.au',
            'password': 'eeeeeeeeeE!',
            'repeat_password': 'eeeeeeeeeE!',
        })
        assert response.status_code == 200
        assert response.request.path == '/register'
        html = response.get_data(as_text=True)
        assert 'Password must contain: one number.' in html

        # Might want to expand this (Just basically same things as above, only a slight change to try to detect 
        # different variations of bad passwords)

    




    