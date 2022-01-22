import feedparser
from dateutil import parser
from django.db import transaction
from django.utils import timezone

from .exceptions import InvalidFeedURL
from .models import RSSFeed, Entry


class RSSFeedService:
    def create(self, feed_url, create_or_update_entries_function=None):
        feed_parser = feedparser.parse(feed_url)

        if not self._is_valid(feed_parser):
            raise InvalidFeedURL

        with transaction.atomic():
            rss_feed = self._get_or_create_rss_feed(feed_url, feed_parser)

            if create_or_update_entries_function:
                create_or_update_entries_function(rss_feed, feed_parser.entries)

            return rss_feed

    @staticmethod
    def _is_valid(feed_parser):
        if feed_parser.status != 200:
            return False
        if 'xml' not in feed_parser.headers['content-type']:
            return False
        return True

    @staticmethod
    def _get_or_create_rss_feed(feed_url, feed_parser):
        try:
            return RSSFeed.objects.get(title__exact=feed_parser.feed.title, feed_url=feed_url)
        except RSSFeed.DoesNotExist:
            # set required fields
            new_rss_feed = RSSFeed(
                title=feed_parser.feed.title,
                feed_url=feed_url,
                last_checked=timezone.now(),
                next_check=RSSFeed.calculate_next_check(),
                last_status=feed_parser.status,
            )
            # set optional fields
            if hasattr(feed_parser.feed, 'description'):
                new_rss_feed.description = feed_parser.feed.description
            if hasattr(feed_parser.feed, 'updated'):
                new_rss_feed.last_update = parser.parse(feed_parser.feed.updated)

            new_rss_feed.save()
            return new_rss_feed


class EntryService:
    def create_or_update(self, rss_feed: RSSFeed, entries=None):
        get_query = dict()
        if entries is None:
            entries = feedparser.parse(rss_feed.feed_url).entries

        for row in entries:
            if hasattr(row, 'link'):
                get_query['url'] = row.link
            if hasattr(row, 'id'):
                get_query['guid'] = row.id
            if hasattr(row, 'title'):
                get_query['title'] = row.title

            try:
                Entry.objects.get(**get_query)
            except Entry.DoesNotExist:
                new_entry = Entry(feed=rss_feed, title=row.title)
                if hasattr(row, 'link'):
                    new_entry.url = row.link
                if hasattr(row, 'id'):
                    new_entry.guid = row.id

                if hasattr(row, 'content'):
                    new_entry.content = row.content[0].value
                elif hasattr(row, 'description'):
                    new_entry.content = row.description

                if hasattr(row, 'published'):
                    new_entry.publish_date = parser.parse(row.published)
                elif hasattr(row, 'updated'):
                    new_entry.publish_date = parser.parse(row.updated)

                new_entry.save()
