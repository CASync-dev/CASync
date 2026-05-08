import unittest
from app import create_app, db
from app.config import TestConfig
from app.models import User
from app.loggedout.loggedout import register, login

# Tests User functionability: registering, logging, password hashing, apis, etc.
class UserTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestConfig())
        self.app.config['WTF_CSRF_ENABLED'] # Disables CSRF during tests
        self.app.config['LOGIN_DISABLED'] = True # Disable @login_required flags, so we can access the apis.
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
        user = User(username='gerald', email='sekai@hotmail.com')
        user.password = 'foo'
        db.session.add(user)
        db.session.commit()

    def test_password_hashing(self):
        u = User(username='greg', email='abcde@fghi.com')
        u.password = 'myawesomepass!'
        self.assertFalse(u.verify_password('notthepass!'))
        self.assertTrue(u.verify_password('myawesomepass!'))

    def test_gravatar(self):
        u = User(username='john', email='john@example.com')
        self.assertEqual(u.avatar(128), ('https://www.gravatar.com/avatar/d4c74594d841139328695756648b6bd6?d=identicon&s=128'))

    def test_change_username(self):
        user = User(username='bot1', email='bottingmail@user.com')
        user.password = 'foobar'

        response = self.client.post('/api/changeusername', data={
            'newuser': 'bot',
        })
        assert response.status_code == 200
        assert len(response.json['success']) == 1
        assert response.json['success'] == 'bot'

        response = self.client.post('/api/changeusername', data={
            'newuser': 'gerald',
        })
        assert response.status_code == 200
        assert len(response.json['error']) == 1
        assert response.json['error'] == "Username already taken."

    def test_change_email(self):
        user = User(username='bot2', email='bottingbox@user.com')
        user.password = 'foobar'

        response = self.client.post('/api/changeemail', data={
            'newemailaddress': 'boxxingbot@user.com',
        })
        assert response.status_code == 200
        assert len(response.json['success']) == 1
        assert response.json['success'] == 'boxxingbot@user.com'

        response = self.client.post('/api/changeemail', data={
            'newemailaddress': 'sekai@hotmail.com',
        })
        assert response.status_code == 200
        assert len(response.json['error']) == 1
        assert response.json['error'] == 'Email already associated with another account.'

        response = self.client.post('/api/changeemail', data={
            'newemailaddress': 'notanemail',
        })
        assert response.status_code == 200
        assert len(response.json['error']) == 1
        assert response.json['error'] == 'Not an Email'

        


