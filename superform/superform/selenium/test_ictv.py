import datetime
import time

from selenium import webdriver
from selenium.webdriver.support.select import Select

channel_name = "A beautiful channel name"
channel_server_fqdn = "0.0.0.0:8000"
channel_ictv_id = "1"
channel_api_key = "aqwxcvbn"

post_title = "A nice post title"
post_description = "A huuuuge description, because we love it this way"
post_publication_date = datetime.date.today()
post_publication_until = datetime.date.today() + datetime.timedelta(1)


def test_selenium_open_superform(driver):
    driver.get("http://127.0.0.1:5000")
    assert "Superform" in driver.title


def test_selenium_auth(driver):
    login_link = driver.find_element_by_link_text('Login')
    login_link.click()
    assert "TestShib Identity Provider Login" in driver.title
    username_field = driver.find_element_by_name("j_username")
    username_field.send_keys("myself")
    password_field = driver.find_element_by_name("j_password")
    password_field.send_keys("myself")
    submit_button = driver.find_element_by_xpath("//input[@value='Login']")
    submit_button.click()
    time.sleep(1)
    assert "Index - Superform" in driver.title


def test_selenium_new_ictv_channel(driver):
    channels_link = driver.find_element_by_link_text('Channels')
    channels_link.click()
    channel_name_field = driver.find_element_by_xpath("//input[@id='inlineFormInputText']")
    assert channel_name_field
    channel_name_field.send_keys(channel_name)
    channel_module_select = Select(driver.find_element_by_xpath("//select[@id='inlineFormCustomSelectModule']"))
    assert channel_module_select
    channel_module_select.select_by_value("ictv")
    submit_button = driver.find_element_by_class_name("fa-plus")
    assert submit_button
    submit_button.click()
    time.sleep(1)


def test_selenium_conf_ictv_channel(driver):
    channels = driver.find_elements_by_link_text('Configure')
    channel = channels[len(channels) - 1]
    channel.click()
    time.sleep(1)
    channel_server_field = driver.find_element_by_name("ictv_server_fqdn")
    assert channel_server_field
    channel_server_field.clear()
    channel_server_field.send_keys(channel_server_fqdn)
    channel_id_field = driver.find_element_by_name("ictv_channel_id")
    assert channel_id_field
    channel_id_field.clear()
    channel_id_field.send_keys(channel_ictv_id)
    channel_api_field = driver.find_element_by_name("ictv_api_key")
    assert channel_api_field
    channel_api_field.clear()
    channel_api_field.send_keys(channel_api_key)
    save_button = driver.find_element_by_xpath("//button[text()='Save Configuration']")
    assert save_button
    save_button.click()
    time.sleep(1)


def test_selenium_add_moderator(driver):
    authorizations_link = driver.find_element_by_link_text('Authorizations')
    authorizations_link.click()
    time.sleep(1)
    expands = driver.find_elements_by_xpath("//button[@aria-controls='collapseOne']")
    expand = expands[-1]
    assert expand
    expand.click()
    username_fields = driver.find_elements_by_xpath("//input[@placeholder='Username']")
    username_field = username_fields[-1]
    assert username_field
    username_field.clear()
    username_field.send_keys("myself")
    auth_select = Select(driver.find_elements_by_xpath("//select[@id='sel1']")[-1])
    assert auth_select
    auth_select.select_by_value("2")
    add_buttons = driver.find_elements_by_link_text("Add")
    add_button = add_buttons[-1]
    assert add_button
    add_button.click()
    update_button = driver.find_element_by_xpath("//button[text()='Update']")
    update_button.click()


def test_selenium_new_post(driver):
    new_link = driver.find_element_by_link_text('New post')
    new_link.click()
    time.sleep(1)
    title_field = driver.find_element_by_xpath("//input[@id='titlepost']")
    assert title_field
    title_field.send_keys(post_title)
    description_field = driver.find_element_by_xpath("//textarea[@id='descriptionpost']")
    assert description_field
    description_field.send_keys(post_description)
    date_from_field = driver.find_element_by_xpath("//input[@id='datefrompost']")
    assert date_from_field
    date_from_field.send_keys(datetime.datetime.strftime(post_publication_date, "%Y-%m-%d"))
    date_until_field = driver.find_element_by_xpath("//input[@id='dateuntilpost']")
    assert date_until_field
    date_until_field.send_keys(datetime.datetime.strftime(post_publication_until, "%Y-%m-%d"))


def test_selenium_delete_channel(driver):
    channels_link = driver.find_element_by_link_text('Channels')
    channels_link.click()
    time.sleep(1)
    delete_buttons = driver.find_elements_by_class_name("fa-trash")
    delete_button = delete_buttons[-1]
    assert delete_button
    delete_button.click()
    confirm_delete_button = driver.find_element_by_xpath("//button[text()='Delete']")
    assert confirm_delete_button
    confirm_delete_button.click()
    time.sleep(1)


def test_selenium_logout(driver):
    user_link = driver.find_element_by_link_text('Me Myself And I')
    assert user_link
    user_link.click()
    logout_link = driver.find_element_by_link_text('Logout')
    assert logout_link
    logout_link.click()
    assert "You are not logged in." in driver.page_source


driver = webdriver.Firefox()
test_selenium_open_superform(driver)
test_selenium_auth(driver)
test_selenium_new_ictv_channel(driver)
test_selenium_conf_ictv_channel(driver)
test_selenium_add_moderator(driver)
test_selenium_new_post(driver)
test_selenium_delete_channel(driver)
test_selenium_logout(driver)
driver.close()
