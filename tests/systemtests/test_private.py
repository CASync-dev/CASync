import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.systemtests.base import BaseSeleniumTest, localHost

from app import db
from app.models import Event
from datetime import datetime, timedelta, timezone

# extends the BaseSeleniumTest class, which sets up the testing var for selenium
class PrivateSeleniumTests(BaseSeleniumTest):
    """Selenium tests for routes requiring a logged in session."""

    def setUp(self):
        # call setup from the base config
        super().setUp()
        # login as gerald to access authenticated pages for testing
        self.driver.get(localHost + "login")
        self.driver.find_element(By.ID, 'username').send_keys('gerald')
        self.driver.find_element(By.ID, 'password').send_keys('foo')
        self.driver.find_element(By.ID, 'log').click()
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

    def test_schedule_events_load(self):
        # navigate to schedule page
        self.driver.find_element(By.ID, 'nav-schedule').click()
        # check url is schedule
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/schedule")
        )
        # check that there are no events for the user (since we haven't added any to the test database yet)
        events = self.driver.find_elements(By.CSS_SELECTOR, "[data-event-id][data-col]")
        self.assertEqual(len(events), 0)
        # manually add an event to the test database for gerald, then refresh the page and check that it appears
        # Wednesday noon UTC of the current ISO week (Mon–Fri); always goes back to the past Monday
        now = datetime.now(timezone.utc)
        monday = now - timedelta(days=now.weekday())
        start_time = (monday + timedelta(days=2)).replace(hour=12, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        event = Event(title="Test Event", start_time=start_time, end_time=end_time, user_id=1)
        db.session.add(event)
        db.session.commit()
        self.driver.refresh()
        # events are rendered via JS fetch after page load, so wait for the card to appear
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-event-id][data-col]"))
        )
        events = self.driver.find_elements(By.CSS_SELECTOR, "[data-event-id][data-col]")
        self.assertEqual(len(events), 1)
        self.assertIn("Test Event", events[0].text)

    def test_schedule_event_create(self):
        self.driver.find_element(By.ID, 'nav-schedule').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/schedule")
        )
        # click the "create event" button to open the modal
        self.driver.find_element(By.ID, 'btn-create-event').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'drawer'))
        )
        # fill out form and submit
        #start and end need to be in the future for the calendar to accept them, so we set them to be 1 day in the future, skipping satuday and sunday.
        # if skipping sat or sun, need to navigate to next week then check for the event
        starts = time.time() + 24*60*60
        is_next_week = False
        if time.localtime(starts).tm_wday == 5: # saturday
            starts += 2*24*60*60
            is_next_week = True
        elif time.localtime(starts).tm_wday == 6: # sunday
            starts += 24*60*60
            is_next_week = True
        ends = starts + 60*60
        start_str = time.strftime("%Y-%m-%dT%H:%M", time.localtime(starts))
        end_str = time.strftime("%Y-%m-%dT%H:%M", time.localtime(ends))
        self.driver.find_element(By.ID, 'event-title').send_keys("Selenium Test Event")
        self.driver.execute_script("document.getElementById('event-start').value = arguments[0]", start_str)
        self.driver.execute_script("document.getElementById('event-end').value = arguments[0]", end_str)
        self.driver.find_element(By.ID, 'submit-event-btn').click()
        #check modal closes
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element((By.ID, 'drawer'))
        )
        # if the event is in the next week, navigate to next week and check for it there, otherwise check for it in the current week
        if is_next_week:
            self.driver.find_element(By.ID, 'btn-next-week').click()
            WebDriverWait(self.driver, timeout=10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-event-id][data-col]"))
            )
        events = self.driver.find_elements(By.CSS_SELECTOR, "[data-event-id][data-col]")
        self.assertEqual(len(events), 1)
        self.assertIn("Selenium Test Event", events[0].text)

    def test_schedule_event_edit(self):
        self.driver.find_element(By.ID, 'nav-schedule').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/schedule")
        )
        # manually add an event to the test database for gerald
        now = datetime.now(timezone.utc)
        monday = now - timedelta(days=now.weekday())
        start_time = (monday + timedelta(days=2)).replace(hour=12, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        event = Event(title="Test Event", start_time=start_time, end_time=end_time, user_id=1)
        db.session.add(event)
        db.session.commit()
        self.driver.refresh()
        # wait for event to load and click it to open the edit modal
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-event-id][data-col]"))
        )
        self.driver.find_element(By.CSS_SELECTOR, "[data-event-id][data-col]").click()
        self.driver.find_element(By.ID, 'edit-event-btn').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'edit-event-modal'))
        )
        # change the title and submit
        title_input = self.driver.find_element(By.ID, 'edit-event-title')
        title_input.clear()
        title_input.send_keys("Edited Test Event")
        self.driver.find_element(By.ID, 'save-edit-btn').click()
        # Wait for the modal to close
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element((By.ID, 'edit-event-modal'))
        )
        # wait for the calendar to re-render with the updated title (fetch is async)
        WebDriverWait(self.driver, timeout=10).until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, "[data-event-id][data-col]"), "Edited Test Event")
        )
        events = self.driver.find_elements(By.CSS_SELECTOR, "[data-event-id][data-col]")
        self.assertEqual(len(events), 1)
        self.assertIn("Edited Test Event", events[0].text)


    def test_friends(self):
        pass

    def test_groups(self):
        pass

    def test_settings(self):
        pass
