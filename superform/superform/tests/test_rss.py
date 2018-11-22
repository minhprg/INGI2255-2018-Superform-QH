import os
import xml.etree.ElementTree as ET
from pathlib import Path

import PyRSS2Gen

from superform import *
from superform.plugins import rss
from superform.utils import datetime_converter


root, current_dir = os.path.split(os.path.dirname(__file__))
root = root + "/plugins/rssfeeds/"


def check_post(pub, path):
    tree = ET.parse(path)
    channel = tree.getroot().find('channel')
    last_item = channel.find('item')

    return last_item.find('title').text == pub.title and last_item.find('description').text == pub.description \
        and last_item.find('link').text == pub.link_url


def count(path):
    tree = ET.parse(path)
    root1 = tree.getroot()
    count1 = 0

    for _ in root1.iter('item'):
        count1 += 1

    return count1


def del_file(path):
    for item in path:
        if Path(item).exists():
            os.remove(item)


def test_create_feed_if_none_exist():
    """
    Test if our module create a new RSS feed (new xml file) if it is the first time a post is send towards this channel.
    It also tests if it added the right post.
    """

    pub = Publishing(title="This is a test feed", description="This is a test description feed", link_url="www.facebook.com", channel_id=-1)

    path = root + "-1.xml"

    del_file([path])

    conf = "{\"feed_title\": \"-\", \"feed_description\": \"-\"}"

    rss.run(pub, conf)

    file = Path(path)

    assert file.exists()

    assert check_post(pub, path)

    del_file([path])


def test_different_channels():
    """
    Test if when publishing on different channels the posts are added to the right feed
    """

    pub1 = Publishing(title="first title", description="first description feed", link_url="www.google.com", channel_id=-2)
    pub2 = Publishing(title="second title", description="second description feed", link_url="www.google.com", channel_id=-3)

    conf1 = "{\"feed_title\": \"-\", \"feed_description\": \"-\"}"
    conf2 = "{\"feed_title\": \"-\", \"feed_description\": \"-\"}"

    path1 = root + '-2.xml'
    path2 = root + '-3.xml'

    del_file([path1, path2])

    rss.run(pub1, conf1)
    rss.run(pub2, conf2)

    assert Path(path1).exists()
    assert Path(path2).exists()

    assert count(path1) == 1
    assert count(path2) == 1

    assert check_post(pub1, path1)
    assert check_post(pub2, path2)

    del_file([path1, path2])


def test_publish_post():
    """
    Test that when adding a new post to a feed it is actually added and added at the top of the feed
    """

    pub = Publishing(title="Voici un super beau titre", description="Avec une super description", link_url="www.facebook.com", date_from="2018-10-25", channel_id=-4)
    conf = "{\"feed_title\": \"-\", \"feed_description\": \"-\"}"

    path = root + "-4.xml"
    rss.run(pub, conf)

    count1 = count(path)

    rss.run(pub, conf)

    assert (count1 < count(path))
    assert check_post(pub, path)

    del_file([path])


def test_delete_old_post():
    """
    Test that if an old post (older than 1 year) is still in the feed it will be deleted
    """
    pub = Publishing(title="Voici un super beau titre", description="Avec une super description", link_url="www.facebook.com", date_from="2018-10-25", channel_id=-5)
    conf = "{\"feed_title\": \"-\", \"feed_description\": \"-\"}"

    path = root + "-5.xml"
    new_rss = rss.create_initial_feed(path)
    item = PyRSS2Gen.RSSItem(
                title=pub.title,
                link=pub.link_url,
                description=pub.description,
                pubDate=datetime_converter('2016-01-01'))

    new_rss.items.insert(0, item)

    with open(path, "w+") as file:
        new_rss.write_xml(file)

    assert count(path) == 1  # Check that the post has been added

    rss.run(pub, conf)
    assert count(path) == 1

    del_file([path])


def test_server_reboot():
    """
    Test that when de server reboots it restore the rss feeds with the xml files already existing and add the new item
    to the corresponding feed. Make sure it don't erase the already existing xml file.
    """

    pub = Publishing(title="Voici un super beau titre", description="Avec une super description", link_url="www.facebook.com", date_from="2018-10-25", channel_id=-6)
    conf = "{\"feed_title\": \"-\", \"feed_description\": \"-\"}"

    path = root + "-6.xml"
    rss.run(pub, conf)

    assert count(path) == 1  # Check that the post has been added
    assert check_post(pub, path)

    rss.rss_feeds = {}  # simulate a server reboot by setting the list of rss feeds to none
    rss.run(pub, conf)

    assert count(path) == 2
    assert check_post(pub, path)


    del_file([path])
