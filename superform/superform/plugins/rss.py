import os

import PyRSS2Gen
import datetime
import feedparser
import json
from pathlib import Path

from lxml import etree

from superform.utils import StatusCode

FIELDS_UNAVAILABLE = ["date_from", "date_until", "image"]
CONFIG_FIELDS = ["feed_title", "feed_description"]
SERVER_URL = "localhost:5000/rss/"
rss_feeds = {}


def add_rss_feed(rss_feed, link):
    feed = feedparser.parse(link)
    for item in feed['items']:
        title = item['title']
        try:
            link = item['link']
        except KeyError:
            link = None

        description = item['description']
        pubdate = item['published']
        new_item = PyRSS2Gen.RSSItem(
            title=title,
            link=link,
            description=description,
            pubDate=pubdate
        )
        rss_feed.items.insert(0, new_item)


def create_initial_feed(feed_url, feed_title="Superform's RSS feed", feed_description="The RSS feed of Superform"):

    rss = PyRSS2Gen.RSS2(
        title=feed_title,
        link=feed_url,
        description=feed_description,
        items=[]
    )

    return rss


def import_xml_to_rss_feed(rss_feed, xml_path):
    tree = etree.parse(xml_path)

    title = list()
    link = list()
    description = list()
    pub_date = list()

    for attrib in tree.xpath("/rss/channel/item/title"):
        title.append(attrib.text)

    for attrib in tree.xpath("/rss/channel/item/link"):
        link.append(attrib.text)

    for attrib in tree.xpath("/rss/channel/item/description"):
        description.append(attrib.text)

    for attrib in tree.xpath("/rss/channel/item/pubDate"):
        try:
            pub_date.append(datetime.datetime.strptime(attrib.text, "%a, %d %b %Y %X %Z"))
        except ValueError:
            try:
                pub_date.append(datetime.datetime.strptime(attrib.text, "%a, %d %b %Y %X %z"))
            except ValueError:
                try:
                    pub_date.append(datetime.datetime.strptime(attrib.text, "%a, %d %b %Y %X GMT"))
                except ValueError:
                    pub_date.append(datetime.datetime.now())

    for i in range(0, len(pub_date)):
        actual_title = None if len(title) <= i else title[i]
        actual_description = None if len(description) <= i else description[i]
        if actual_title is not None or actual_description is not None:
            item = PyRSS2Gen.RSSItem(
                title=None if len(title) <= i else title[i],
                link=None if len(link) <= i else link[i],
                description=None if len(description) <= i else description[i],
                pubDate=pub_date[i]
            )
            rss_feed.items.append(item)


def run(publishing, channel_config):

    global rss_feeds

    json_data = json.loads(channel_config)
    rss_feed_title = json_data["feed_title"]
    rss_feed_description = json_data["feed_description"]
    rss_plugin_path = os.path.dirname(__file__)
    channel_id = publishing.channel_id
    rss_feed_local_file_path = rss_plugin_path + "/rssfeeds/" + str(channel_id) + ".xml"
    rss_feed_url = SERVER_URL + str(channel_id) + ".xml"

    if (publishing.title is None or publishing.title == "") and (publishing.description is None or publishing.description == ""):
        return StatusCode.ERROR, 'You need to enter at least a title or a description', None

    if channel_id not in rss_feeds:
        rss_feeds[channel_id] = create_initial_feed(feed_url=rss_feed_url, feed_title=rss_feed_title, feed_description=rss_feed_description)
        if Path(rss_feed_local_file_path).exists():
            import_xml_to_rss_feed(rss_feeds[channel_id], rss_feed_local_file_path)

    pub_date = datetime.datetime.now()

    if publishing.rss_feed is not None:
        add_rss_feed(rss_feeds[channel_id], publishing.rss_feed)

    item = PyRSS2Gen.RSSItem(
                title=publishing.title,
                link=publishing.link_url,
                description=publishing.description,
                pubDate=pub_date)

    rss_feeds[channel_id].items.insert(0, item)

    with open(rss_feed_local_file_path, "w+") as file:
        rss_feeds[channel_id].write_xml(file)

    return StatusCode.OK, None, None
