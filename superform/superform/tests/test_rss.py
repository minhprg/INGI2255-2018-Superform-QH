import unittest
import xml.etree.ElementTree as ET
import os
from pathlib import Path


from superform import *
from superform.plugins import rss

class TestRSS(unittest.TestCase):

    def test_create_feed_if_none_exist(self):
        pub = Publishing(title="coucou", description="ta mere", link_url="www.facebook.com")
        os.system("rm /Users/maxime/serv/rss.xml")

        conf = "{\"feedUrl\": \"/Users/maxime/serv/rss.xml\"}"

        rss.run(pub, conf)

        file = Path("/Users/maxime/serv/rss.xml")

        self.assertTrue(file.exists())

    def test_publish_post(self):
        pub = Publishing(title="Voici un super beau titre", description="Avec une super description", link_url="www.facebook.com", date_from="2018-10-25")
        conf = "{\"feedUrl\": \"/Users/maxime/serv/rss.xml\"}"

        rss.run(pub, conf)

        tree = ET.parse('/Users/maxime/serv/rss.xml')
        root = tree.getroot()

        count1 = 0

        for child in root.iter('item'):
            count1 += 1

        rss.run(pub, conf)

        tree1 = ET.parse('/Users/maxime/serv/rss.xml')
        root1 = tree1.getroot()

        count2 = 0
        for child in root1.iter('item'):
            count2 += 1

        self.assertTrue(count1 < count2)


if __name__ == '__main__':
    unittest.main(verbosity=2)