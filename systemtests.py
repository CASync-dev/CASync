import multiprocessing
import threading
import time
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app import create_app, db
from app.config import TestConfig
from app.models import User # Just to use the TestCase! Not really an unit test...

localHost = "http://127.0.0.1:9000/" # localhost url to be passed to driver.
# If Github won't run the app at this port since something else is using it, change the port until it does.

class SeleniumTests(unittest.TestCase):
    client = None
    @classmethod
    def setUpClass(cls):
        try:
            cls.client = webdriver.Firefox()
        except:
            pass

        if cls.client:
            cls.app = create_app(config_class=TestConfig)
            cls.app_context = cls.app.app_context()
            cls.app_context.push()

            db.create_all()
            cls.populate_db()

            options = webdriver.FirefoxOptions()
            options.add_argument("--headless")
            cls.driver = webdriver.Firefox(options=options)

            cls.server_thread = threading.Thread(target=cls.app.run, kwargs={'port':9000})
            cls.server_thread.start()

            time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        if cls.client:
            cls.client.get('http://127.0.0.1:9000/shutdown') # Calls route that shuts down the app.
            cls.client.quit()
            db.session.remove()
            db.drop_all()
            cls.app_context.pop()
        
    def populate_db():
        user = User(username='gerald', email='gerald@hotmail.com') # userid = 1
        user.password = 'foo'
        db.session.add(user)
        db.session.commit()

    def setUp(self):
        if not self.client:
            self.skipTest('Web browser not available')

    def tearDown(self):
        pass
    
    def test_index(self):
        pass

    def test_faq(self):
        pass

    def test_contact_us(self):
        pass

    def test_register(self):
        pass

    def test_loginlogout(self):
        self.driver.get(localHost + "login") #Gets login url

        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'login'))
        )

        self.driver.find_element(By.ID, 'username').send_keys("gerald")
        self.driver.find_element(By.ID, 'password').send_keys("foo")
        self.driver.find_element(By.ID, 'log').click()

        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'title_username'))
        )

        greeting = self.driver.find_element(By.ID, 'title_username')
        self.assertEqual(greeting.text, 'Hello, gerald!')

        self.driver.find_element(By.ID, 'logout').click()

        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'login'))
        )
        msg = self.driver.find_element(By.ID, 'msg')
        self.assertEqual(msg.text, 'You have been logged out.')

    def test_login_incorrect(self):
        self.driver.get(localHost + "login") #Gets login url

        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'login'))
        )

        self.driver.find_element(By.ID, 'username').send_keys("gerald")
        self.driver.find_element(By.ID, 'password').send_keys("bar")
        self.driver.find_element(By.ID, 'log').click()

        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'login'))
        )

        error = self.driver.find_element(By.ID, 'msg')
        self.assertEqual(error.text, 'Invalid username or password')

        self.driver.find_element(By.ID, 'username').send_keys("fakeuser")
        self.driver.find_element(By.ID, 'password').send_keys("bar")
        self.driver.find_element(By.ID, 'log').click()

        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'login'))
        )

        error = self.driver.find_element(By.ID, 'msg')
        self.assertEqual(error.text, 'Invalid username or password')

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