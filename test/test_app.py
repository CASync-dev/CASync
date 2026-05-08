import unittest
from app import create_app
from flask import current_app

from app.config import TestConfig
# Do tests on this non-persistent database

# Tests App functionability
class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestConfig())
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        self.app_context.pop()
        self.app = None
        self.app_context = None

    def test_app(self):
        assert self.app is not None
        assert current_app == self.app

    # Testing if auth only pages block users that aren't logged in.
    def test_dash_redirect(self):
        response = self.client.get('/dash', follow_redirects=True)
        assert response.status_code == 200
        assert response.request.path == '/login'

    def test_schedule_redirect(self):
        response = self.client.get('/schedule', follow_redirects=True)
        assert response.status_code == 200
        assert response.request.path == '/login'

    def test_schedule_redirect(self):
        response = self.client.get('/groups', follow_redirects=True)
        assert response.status_code == 200
        assert response.request.path == '/login'

    def test_schedule_redirect(self):
        response = self.client.get('/friends', follow_redirects=True)
        assert response.status_code == 200
        assert response.request.path == '/login'

    def test_schedule_redirect(self):
        response = self.client.get('/settings', follow_redirects=True)
        assert response.status_code == 200
        assert response.request.path == '/login'
    
