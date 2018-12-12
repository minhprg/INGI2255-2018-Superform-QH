from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import random
import string
import time
import unittest


class Post(unittest.TestCase):

    r = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=16))

    def setUp(self):
        self.driver = webdriver.Chrome()

    def test_1_new_post_linkedin_facebook(self):
        driver = self.driver
        # go to the google home page
        driver.get("https://127.0.0.1:5000/login")
        driver.find_element(By.NAME, "j_username").send_keys("myself")
        pwd = driver.find_element(By.NAME, "j_password")
        pwd.send_keys("myself")
        pwd.submit()
        driver.get("https://127.0.0.1:5000/new")
        assert "New" in driver.title
        driver.find_element(By.NAME, "titlepost").send_keys("this is a random text: " + self.r)
        driver.find_element(By.NAME, "descriptionpost").send_keys("this is a random text: " + self.r)
        driver.find_element(By.NAME, "linkurlpost").send_keys("https://www.seleniumhq.org")
        driver.find_element(By.NAME, "datefrompost").send_keys("12052018")
        driver.find_element(By.NAME, "timefrompost").send_keys("1200PM")
        driver.find_element(By.NAME, "dateuntilpost").send_keys("12062018")
        driver.find_element(By.NAME, "timeuntilpost").send_keys("1200PM")
        driver.find_element(By.ID, "chan_option_1").click()
        driver.find_element(By.ID, "chan_option_2").click()
        driver.find_element(By.ID, "publish-button").click()
        assert "Index" in driver.title

    def test_2_publish(self):
        driver = self.driver
        driver.get("https://127.0.0.1:5000/login")
        driver.find_element(By.NAME, "j_username").send_keys("alterego")
        pwd = driver.find_element(By.NAME, "j_password")
        pwd.send_keys("alterego")
        pwd.submit()
        driver.find_element(By.LINK_TEXT, "Moderate").click()
        driver.find_element(By.ID, "publish-button").click()
        assert "Index" in driver.title

        self.check_linkedin(self.r)
        self.check_facebook(self.r)


    def check_linkedin(self, text):
        driver = self.driver
        # Open linked in
        driver.get("https://www.linkedin.com/")
        if EC.title_contains("Logg In"):
            driver.find_element(By.NAME, "session_key").send_keys("spam001@hotmail.be")
            pwd = driver.find_element(By.NAME, "session_password")
            pwd.send_keys("test1234")
            pwd.submit()

        # time.sleep(60 * 1)
        driver.get("https://www.linkedin.com/company/12654611/admin/")

        try:
            # driver.find_elements_by_xpath("//*[contains(text(), "+text+")]")
            driver.find_elements_by_xpath("//*[contains(text(),  'this is a random text:')]")
        except:
            assert False

    def check_facebook(self, text):
        driver = self.driver
        driver.get("https://www.facebook.com/")
        driver.find_element(By.NAME, "email").send_keys("superform@moff.be")
        pwd = driver.find_element(By.NAME, "pass")
        pwd.send_keys("testsuperform")
        pwd.submit()
        driver.get("https://www.facebook.com/Testsuperform-1625488667557071/?notif_id=1544184537965808&notif_t=page_admin")

        try:
            #driver.find_elements_by_xpath("//*[contains(text(), " + text + ")]")
            driver.find_elements_by_xpath("//*[contains(text(),  'this is a random text:')]")
        except:
            assert False

    def tearDown(self):
        self.driver.close()

if __name__ == "__main__":

    unittest.main()


