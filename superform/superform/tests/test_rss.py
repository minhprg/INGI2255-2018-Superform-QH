import xml.etree.ElementTree as ET
import os
from pathlib import Path


from superform import *
from superform.plugins import rss


local_feed_url = 'rss.xml'


def test_create_feed_if_none_exist():
    pub = Publishing(title="This is a test feed", description="This is a test description feed", link_url="www.facebook.com")
    os.system("rm ../plugins/rssfeeds/" + local_feed_url)

    conf = "{\"local_feed_url\": \"" + str(local_feed_url) + "\", \"feed_url\": \"-\", \"feed_title\": \"-\", \"feed_description\": \"-\"}"

    rss.run(pub, conf)

    file = Path('../plugins/rssfeeds/' + local_feed_url)

    assert file.exists() == True


def test_publish_post():
    pub = Publishing(title="Voici un super beau titre", description="Avec une super description", link_url="www.facebook.com", date_from="2018-10-25")
    conf = "{\"local_feed_url\": \"" + local_feed_url + "\", \"feed_url\": \"-\", \"feed_title\": \"-\", \"feed_description\": \"-\"}"

    rss.run(pub, conf)

    tree = ET.parse("../plugins/rssfeeds/" + local_feed_url)
    root = tree.getroot()

    count1 = 0

    for child in root.iter('item'):
        count1 += 1

    rss.run(pub, conf)

    tree1 = ET.parse("../plugins/rssfeeds/" + local_feed_url)
    root1 = tree1.getroot()

    count2 = 0
    for child in root1.iter('item'):
        count2 += 1

    assert (count1 < count2) == True

