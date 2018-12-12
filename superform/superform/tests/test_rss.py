import os
import xml.etree.ElementTree as ET
from pathlib import Path

from superform import *
from superform.plugins import rss
from superform.plugins.rss import create_initial_feed, import_xml_to_rss_feed
from superform.utils import StatusCode

parent_root, current_dir = os.path.split(os.path.dirname(__file__))
root = parent_root + "/plugins/rssfeeds/"


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


def import_xml_to_rss(file, length=3):
    path = parent_root + '/tests/test_rss_xmls/' + file
    file = Path(path)

    assert file.exists()

    rss_feed = create_initial_feed(feed_url=path)
    try:
        import_xml_to_rss_feed(rss_feed, path)
        assert len(rss_feed.items) == length
        return rss_feed
    except IndexError or TypeError:
        assert False


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


def test_non_valid_publishing():
    pub = Publishing(link_url="www.facebook.com", date_from="2018-10-25", channel_id=-7)
    conf = "{\"feed_title\": \"-\", \"feed_description\": \"-\"}"

    path = root + "-7.xml"

    response = rss.run(pub, conf)
    assert type(response) is tuple
    assert response[0] == StatusCode.ERROR
    assert response[2] is None

    file = Path(path)
    assert not file.exists()


def test_import_xml_to_rss_feed():
    import_xml_to_rss('test_normal.xml')


def test_import_xml_to_rss_feed_no_link():
    rss_feed = import_xml_to_rss('test_no_link.xml')
    for item in rss_feed.items:
        assert item.link is None


def test_import_xml_to_rss_feed_empty_link():
    rss_feed = import_xml_to_rss('test_empty_link.xml')
    for item in rss_feed.items:
        assert item.link is None


def test_import_xml_to_rss_feed_no_title():
    rss_feed = import_xml_to_rss('test_no_title.xml', length=1)
    for item in rss_feed.items:
        assert item.title is None


def test_import_xml_to_rss_feed_empty_title():
    rss_feed = import_xml_to_rss('test_empty_title.xml', length=1)
    for item in rss_feed.items:
        assert item.title is None

