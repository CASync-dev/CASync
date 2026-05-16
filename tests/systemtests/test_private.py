import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.systemtests.base import BaseSeleniumTest, localHost


class PrivateSeleniumTests(BaseSeleniumTest):
    """Selenium tests for routes requiring an authenticated session."""

    def setUp(self):
        super().setUp()
        # login as gerald to access authenticated pages for testing
        self.driver.get(localHost + "login")
        self.driver.find_element(By.ID, 'username').send_keys('gerald')
        self.driver.find_element(By.ID, 'password').send_keys('foo')
        self.driver.find_element(By.ID, 'login').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/dash")
        )

    def tearDown(self):
        # logout after each test to ensure a clean slate for the next one
        self.driver.find_element(By.ID, 'logout').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/login")
        )

    def test_dash(self):
        pass

    def test_schedule_navigation(self):
        # click schedule link
        self.driver.find_element(By.ID, 'nav-schedule').click()
        # check url is schedule
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/schedule")
        )
        # check calender title is todays date (Today, Day Mon DD)
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
        # check today nav button works
        self.driver.find_element(By.ID, 'btn-today').click()
        calendarTitle = self.driver.find_element(By.ID, 'calendar-title')
        self.assertEqual(calendarTitle.text, initialTitle)
        # check previous week nav button works
        self.driver.find_element(By.ID, 'btn-last-week').click()
        calendarTitle = self.driver.find_element(By.ID, 'calendar-title')
        prev_week = time.strftime("%a %b %-d", time.localtime(time.time() - 7*24*60*60))
        expected_title = "Last Week, " + prev_week
        self.assertEqual(calendarTitle.text, expected_title)
        # go back to current week so tearDown's logout has a clean state
        self.driver.find_element(By.ID, 'btn-today').click()

    def test_schedule_events(self):
        # navigate to schedule page
        self.driver.find_element(By.ID, 'nav-schedule').click()
        # check url is schedule
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/schedule")
        )
        # check that there are no events for the user (since we haven't added any to the test database yet)
        events = self.driver.find_elements(By.CLASS_NAME, 'event')
        self.assertEqual(len(events), 0)

    def test_friends(self):
        pass

    def test_groups(self):
        pass

    def test_settings(self):
        pass
