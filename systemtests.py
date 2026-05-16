import multiprocessing
import os
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

# Set HEADLESS=0 to watch the browser run the tests; defaults to headless for CI.
HEADLESS = os.environ.get("HEADLESS", "1") != "0"

class SeleniumTests(unittest.TestCase):
    # We initialize the WebDriver as a class variable so that it can be shared across all test methods, which speeds up the testing process since we don't have to start a new browser for each test.
    driver = None
    @classmethod
    # Set up the test class by starting the Flask app in a separate thread and initializing the Selenium WebDriver. 
    # We use a class method so that the setup is done once for all tests, which speeds up the testing process.
    def setUpClass(cls):
        options = webdriver.FirefoxOptions()
        # Default runs in headless mode, sometimes its fun to watch it tho
        if HEADLESS:
            options.add_argument("--headless")
        try:
            cls.driver = webdriver.Firefox(options=options)
        except Exception:
            return

        # Set up Flask app context and database for testing
        cls.app = create_app(config_class=TestConfig)
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

        # Create all tables and populate with initial data for testing
        db.create_all()
        cls.populate_db()

        # Start the Flask app in a separate thread so that it can handle requests from the Selenium WebDriver during testing
        # We set use_reloader=False to prevent the app from starting multiple times, and daemon=True so that it will automatically close when the main thread finishes.
        cls.server_thread = threading.Thread(
            target=cls.app.run,
            kwargs={'port': 9000, 'use_reloader': False},
            daemon=True, #alternatively we could call driver.quit() in tearDownClass, but this is simpler and ensures the server will stop even if something goes wrong with the tests
        )
        cls.server_thread.start()

        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        # Quit the Selenium WebDriver and clean up the Flask app context and database after all tests have run
        if cls.driver:
            cls.driver.quit()
            db.session.remove()
            db.drop_all()
            cls.app_context.pop()
        
        
    @classmethod
    def populate_db(cls):
        user = User(username='gerald', email='gerald@hotmail.com') # userid = 1
        user.password = 'foo'
        db.session.add(user)
        db.session.commit()

    def setUp(self):
        if not self.driver:
            self.skipTest('Web browser not available')

    def tearDown(self):
        pass
    
    def test_index(self):
        self.driver.get(localHost) #Gets homepage url


    def test_faq(self):
        self.driver.get(localHost) #Gets homepage url
        self.driver.find_element(By.ID, 'faq').click() #Clicks FAQ link
        # check url is correct
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/faq")
        )
        faqTitle = self.driver.find_element(By.TAG_NAME, "h1")
        assert faqTitle.text == "Frequently Asked Questions" 

    def test_contact_us(self):
        self.driver.get(localHost) #Gets homepage url
        self.driver.find_element(By.ID, 'contactus').click() #Clicks Contact Us link
        # check url is correct
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/contactus")
        )
        contactTitle = self.driver.find_element(By.TAG_NAME, "h1")
        assert contactTitle.text == "Contact Us"

    def test_register(self):
        self.driver.get(localHost) #Gets homepage url
        self.driver.find_element(By.ID, 'register').click() #Clicks the register link
        # check url is correct
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/register")
        )
        # Register a new user
        self.driver.find_element(By.ID, 'email').send_keys("newuser@example.com")
        self.driver.find_element(By.ID, 'username').send_keys("newuser")
        self.driver.find_element(By.ID, 'password').send_keys("Newpassword1234!")
        self.driver.find_element(By.ID, 'repeat_password').send_keys("Newpassword1234!")
        self.driver.find_element(By.ID, 'log').click()
        # check url is dash
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/dash")
        )
        # check that the greeting is correct
        greeting = self.driver.find_element(By.ID, 'title_username')
        self.assertEqual(greeting.text, 'Hello, newuser!')
        # Logout the new user
        self.driver.find_element(By.ID, 'logout').click()
        # check url is login
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/login")
        )

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
        self.driver.get(localHost + "login") #Gets homepage url
        # login
        self.driver.find_element(By.ID, 'username').send_keys("gerald")
        self.driver.find_element(By.ID, 'password').send_keys("foo")
        self.driver.find_element(By.ID, 'log').click()
        # check url is dash
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/dash")
        )
        # click schedule link
        self.driver.find_element(By.ID, 'nav-schedule').click()
        # check url is schedule
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/schedule")
        )
        #check calender title is todays date (Today, Day Mon DD)
        calendarTitle = self.driver.find_element(By.ID, 'calendar-title')
        today = time.strftime("%a %b %d")
        initialTitle = "Today, " + today
        self.assertEqual(calendarTitle.text, initialTitle)
        # check next week nav buttons work
        self.driver.find_element(By.ID, 'btn-next-week').click()
        calendarTitle = self.driver.find_element(By.ID, 'calendar-title')
        nextWeek = time.strftime("%a %b %d", time.localtime(time.time() + 7*24*60*60))
        expectedTitle = "Next Week, " + nextWeek
        self.assertEqual(calendarTitle.text, expectedTitle)

    def test_friends(self):
        pass

    def test_groups(self):
        pass

    def test_settings(self):
        pass