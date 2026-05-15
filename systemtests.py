import multiprocessing
import unittest
from selenium import webdriver
from app import create_app, db
from app.config import TestConfig # Just to use the TestCase! Not really an unit test...

localHost = "http://127.0.0.1:9000/" # localhost url to be passed to driver.
# If Github won't run the app at this port since something else is using it, change the port until it does.

class SeleniumTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context
        self.app_context.push()
        db.create_all()
        self.populate_db()

        self.server_thread = multiprocessing.Process(target=self.app.run)
        self.server_thread.start()

        self.driver = webdriver.Firefox()
        self.driver.get(localHost)
        self.headlessMode() # Disable to enable creating browser window for test
        return super().setUp()

    def headlessMode(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        self.driver = webdriver.Chrome(options=options)

    def tearDown(self):
        self.server_thread.terminate()
        self.driver.close()
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        return super().tearDown()
        
    def populate_db(self):
        pass

    def test_index(self):
        pass

    def test_faq(self):
        pass

    def test_contact_us(self):
        pass

    def test_register(self):
        pass

    def test_login(self):
        pass

    def test_dash(self):
        pass
    
    def test_schedule(self):
        pass

    def test_friends(self):
        pass

    def test_groups(self):
        pass

    def test_settings(self):
        pass