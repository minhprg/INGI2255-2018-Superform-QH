import unittest
import xml.etree.ElementTree as ET

from superform import *
from superform.plugins import rss

class TestRSS(unittest.TestCase):

    def test_publish_post(self):
        pub = Publishing(title="coucou", description="ta mere", link_url="www.facebook.com")
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