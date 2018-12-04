import time

from selenium import webdriver
from selenium.webdriver.support.select import Select


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
    channel_name_field.send_keys("A beautiful channel name")
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
    channel_server_field.send_keys("example")
    channel_id_field = driver.find_element_by_name("ictv_channel_id")
    assert channel_id_field
    channel_id_field.send_keys("example")
    channel_api_field = driver.find_element_by_name("ictv_api_key")
    assert channel_api_field
    channel_api_field.send_keys("example")
    save_button = driver.find_element_by_xpath("//button[text()='Save Configuration']")
    assert save_button
    save_button.click()
    time.sleep(1)


driver = webdriver.Firefox()
test_selenium_open_superform(driver)
test_selenium_auth(driver)
test_selenium_new_ictv_channel(driver)
test_selenium_conf_ictv_channel(driver)
driver.close()
