import os
import xml.etree.ElementTree as ET
from pathlib import Path

from superform import *
from superform.plugins import rss


def count(element):
    count1 = 0

    for _ in element.iter('item'):
        count1 += 1

    return count1


def del_file(path):
    for item in path:
        if Path(item).exists():
            os.remove(item)


def test_create_feed_if_none_exist():
    pub = Publishing(title="This is a test feed", description="This is a test description feed", link_url="www.facebook.com", channel_id=-1)

    del_file(['../plugins/rssfeeds/-1.xml'])

    conf = "{\"feed_title\": \"-\", \"feed_description\": \"-\"}"

    rss.run(pub, conf)

    file = Path('../plugins/rssfeeds/-1.xml')

    assert file.exists()

    del_file(['../plugins/rssfeeds/-1.xml'])


def test_different_channels():
    pub1 = Publishing(title="first title", description="first description feed", link_url="www.google.com", channel_id=-2)
    pub2 = Publishing(title="second title", description="second description feed", link_url="www.google.com", channel_id=-3)

    conf1 = "{\"feed_title\": \"-\", \"feed_description\": \"-\"}"
    conf2 = "{\"feed_title\": \"-\", \"feed_description\": \"-\"}"

    del_file(['../plugins/rssfeeds/-2.xml', '../plugins/rssfeeds/-3.xml'])

    rss.run(pub1, conf1)
    rss.run(pub2, conf2)

    assert Path('../plugins/rssfeeds/-2.xml').exists()
    assert Path('../plugins/rssfeeds/-3.xml').exists()

    tree1 = ET.parse("../plugins/rssfeeds/-2.xml")
    tree2 = ET.parse("../plugins/rssfeeds/-3.xml")

    root1 = tree1.getroot()
    root2 = tree2.getroot()

    assert count(root1) == 1
    assert count(root2) == 1

    del_file(['../plugins/rssfeeds/-2.xml', '../plugins/rssfeeds/-3.xml'])


def test_publish_post():
    pub = Publishing(title="Voici un super beau titre", description="Avec une super description", link_url="www.facebook.com", date_from="2018-10-25", channel_id=-4)
    conf = "{\"feed_title\": \"-\", \"feed_description\": \"-\"}"

    rss.run(pub, conf)

    tree = ET.parse("../plugins/rssfeeds/-4.xml")
    root = tree.getroot()

    rss.run(pub, conf)

    tree1 = ET.parse("../plugins/rssfeeds/-4.xml")
    root1 = tree1.getroot()

    assert (count(root) < count(root1))

    del_file(["../plugins/rssfeeds/-4.xml"])

