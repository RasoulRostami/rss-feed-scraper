import json
from datetime import timedelta
from unittest import mock
from uuid import uuid4

from cerberus import Validator
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.account.tests.factories import UserFactory
from .factories import RSSFeedFactory, EntryFactory, EntryCommentFactory
from .mocks import FakerRssFeedParse, FakeLimitError
from .schemas import (
    rss_feed_list_schema,
    entry_list_schema,
    entry_schema,
    entry_comment_list_schema,
    entry_comment_schema,
    feed_schema_after_create,
)
from ..models import RSSFeed, RSSFeedFollower, Entry, BookmarkedEntry, SeenEntry, FavouritedEntry, EntryComment
from ..tasks import update_feeds


class RSSFeedListTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = '/api/v1/rss/feeds/'
        cls.active_feed_1 = RSSFeedFactory()
        cls.active_feed_2 = RSSFeedFactory()
        cls.inactive_feed = RSSFeedFactory(is_active=False)
        cls.user = UserFactory()

    def test_status_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_schema(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        schema_validator = Validator(rss_feed_list_schema)
        self.assertTrue(schema_validator.validate(json.loads(response.content)), msg=schema_validator.errors)

    def test_filter_is_active(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.data['count'], RSSFeed.objects.count())  # without filter, return all
        response = self.client.get(f"{self.url}?is_active=true")
        self.assertEqual(response.data['count'], RSSFeed.objects.filter(is_active=True).count())
        response = self.client.get(f"{self.url}?is_active=false")
        self.assertEqual(response.data['count'], RSSFeed.objects.filter(is_active=False).count())

    def test_search_title(self):
        self.client.force_login(self.user)
        response = self.client.get(f"{self.url}?search={self.active_feed_1.title}")
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], self.active_feed_1.title)

    def test_search_link(self):
        self.client.force_login(self.user)
        response = self.client.get(f"{self.url}?search={self.active_feed_2.feed_url}")
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['feed_url'], self.active_feed_2.feed_url)

    def test_is_followed_filter(self):
        self.active_feed_1.follow(self.user)
        self.client.force_login(self.user)
        response = self.client.get(f"{self.url}?is_followed=true")
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.active_feed_1.id))
        self.assertEqual(
            response.data['results'][0]['number_of_followers'], RSSFeedFollower.objects.filter(feed=self.active_feed_1).count()
        )

    def test_is_followed_field_value(self):
        self.active_feed_1.follow(self.user)
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        for result in response.data['results']:
            if result['id'] == str(self.active_feed_1.id):
                self.assertTrue(result['is_followed'])
            else:
                self.assertFalse(result['is_followed'])

    def test_number_of_followers_value(self):
        self.active_feed_1.follow(self.user)
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        for result in response.data['results']:
            self.assertEqual(result['number_of_followers'], RSSFeedFollower.objects.filter(feed_id=result['id']).count())

    def test_number_of_unseen_entries_when_user_has_not_followed_feed(self):
        EntryFactory(feed=self.active_feed_1)
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        for result in response.data['results']:
            self.assertEqual(result['number_of_unseen_entries'], 0)

    def test_number_of_unseen_entries_when_user_has_followed_feed(self):
        self.active_feed_1.follow(self.user)
        EntryFactory(feed=self.active_feed_1)
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        for result in response.data['results']:
            if result['id'] == str(self.active_feed_1.id):
                self.assertEqual(result['number_of_unseen_entries'], 1)
            else:
                self.assertEqual(result['number_of_unseen_entries'], 0)


class RSSFeedFollowTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = '/api/v1/rss/feeds/follow/'
        cls.active_feed_1 = RSSFeedFactory()
        cls.inactive_feed = RSSFeedFactory(is_active=False)

        cls.user = UserFactory()
        cls.auth_client = APIClient()
        cls.auth_client.force_login(cls.user)

    def test_status_401(self):
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_follow_400(self):
        response = self.auth_client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.auth_client.patch(self.url, {'feed_id': uuid4()})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unfollow_400(self):
        response = self.auth_client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.auth_client.delete(self.url, {'feed_id': uuid4()})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_follow(self):
        response = self.auth_client.patch(self.url, {'feed_id': self.active_feed_1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.active_feed_1.is_followed_by_user(self.user))
        self.assertTrue(RSSFeedFollower.objects.filter(feed=self.active_feed_1, user=self.user).exists())

        response = self.auth_client.patch(self.url, {'feed_id': self.inactive_feed.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.inactive_feed.is_followed_by_user(self.user))
        self.assertTrue(RSSFeedFollower.objects.filter(feed=self.inactive_feed, user=self.user).exists())

    def test_duplicate_follow_request(self):
        self.active_feed_1.follow(self.user)
        response = self.auth_client.patch(self.url, {'feed_id': self.active_feed_1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.active_feed_1.is_followed_by_user(self.user))
        self.assertTrue(RSSFeedFollower.objects.filter(feed=self.active_feed_1, user=self.user).exists())

    def test_unfollow(self):
        self.active_feed_1.follow(self.user)
        response = self.auth_client.delete(self.url, {'feed_id': self.active_feed_1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.active_feed_1.is_followed_by_user(self.user))
        self.assertFalse(RSSFeedFollower.objects.filter(feed=self.active_feed_1, user=self.user).exists())

    def test_unfollow_when_user_has_not_followed(self):
        response = self.auth_client.delete(self.url, {'feed_id': self.active_feed_1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.active_feed_1.is_followed_by_user(self.user))
        self.assertFalse(RSSFeedFollower.objects.filter(feed=self.active_feed_1, user=self.user).exists())


class EntryListTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.feed_1 = RSSFeedFactory()
        cls.feed_2 = RSSFeedFactory()

        cls.entry_1_1 = EntryFactory(feed=cls.feed_1)
        cls.entry_1_2 = EntryFactory(feed=cls.feed_1)
        cls.entry_2_1 = EntryFactory(feed=cls.feed_2)
        cls.entry_2_2 = EntryFactory(feed=cls.feed_2)

        cls.user = UserFactory()
        cls.auth_client = APIClient()
        cls.auth_client.force_login(cls.user)

    def get_url(self, feed=None, entry=None):
        url = f'/api/v1/rss/entries/'
        if entry:
            url += f'{entry.id}/'
        if feed:
            url += f'?feed_id={feed.id}'
        return url

    def test_response_401(self):
        response = self.client.get(self.get_url(self.feed_1))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_entries_of_feed_1(self):
        response = self.auth_client.get(self.get_url(self.feed_1))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], Entry.objects.filter(feed_id=self.feed_1.id).count())

    def test_bookmarked_entries(self):
        self.entry_1_1.add_bookmark(self.user)
        self.assertTrue(BookmarkedEntry.objects.filter(entry=self.entry_1_1, user=self.user).exists())

        url = f"{self.get_url()}?is_bookmarked=true"
        response = self.auth_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], BookmarkedEntry.objects.filter(user=self.user).count())
        for result in response.data['results']:
            if result['id'] == str(self.entry_1_1.id):
                self.assertTrue(result['is_bookmarked'])
        # check for another user
        client = APIClient()
        client.force_login(UserFactory())
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        for result in response.data['results']:
            if result['id'] == str(self.entry_1_1.id):
                self.assertFalse(result['is_bookmarked'])

    def test_favourite_entries(self):
        self.entry_2_1.add_favourite(self.user)
        self.assertTrue(FavouritedEntry.objects.filter(entry=self.entry_2_1, user=self.user).exists())

        url = f"{self.get_url()}?is_favourited=true"
        response = self.auth_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], FavouritedEntry.objects.filter(user=self.user).count())
        for result in response.data['results']:
            if result['id'] == str(self.entry_2_1.id):
                self.assertTrue(result['is_favourited'])
        # check for another user
        client = APIClient()
        client.force_login(UserFactory())
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_feed_id_filter(self):
        response = self.auth_client.get(self.get_url(feed=self.feed_1))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], Entry.objects.filter(feed=self.feed_1).count())

    def test_seen_filter(self):
        self.entry_2_2.seen(self.user)
        response = self.auth_client.get(f"{self.get_url()}?is_seen=True")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], SeenEntry.objects.filter(user=self.user).count())
        self.assertTrue(SeenEntry.objects.filter(user=self.user))

    def test_schema(self):
        response = self.auth_client.get(self.get_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        schema_validator = Validator(entry_list_schema)
        self.assertTrue(schema_validator.validate(json.loads(response.content)), msg=schema_validator.errors)


class EntryRetrieveTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.feed_1 = RSSFeedFactory()
        cls.feed_2 = RSSFeedFactory()

        cls.entry_1_1 = EntryFactory(feed=cls.feed_1)
        cls.entry_1_2 = EntryFactory(feed=cls.feed_1)
        cls.entry_2_1 = EntryFactory(feed=cls.feed_2)
        cls.entry_2_2 = EntryFactory(feed=cls.feed_2)

        cls.user = UserFactory()
        cls.auth_client = APIClient()
        cls.auth_client.force_login(cls.user)

    def get_url(self, entry):
        return f'/api/v1/rss/entries/{entry.id}/'

    def test_schema(self):
        response = self.auth_client.get(self.get_url(self.entry_1_1))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        schema_validator = Validator(entry_schema)
        self.assertTrue(schema_validator.validate(json.loads(response.content)), msg=schema_validator.errors)

    def test_seen_after_retrieve_when_user_has_not_followed_feed(self):
        self.assertFalse(SeenEntry.objects.filter(user=self.user, entry=self.entry_1_2).exists())
        response = self.auth_client.get(self.get_url(self.entry_1_2))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(SeenEntry.objects.filter(user=self.user, entry=self.entry_1_2).exists())

    def test_seen_after_retrieve_when_user_has_followed_feed(self):
        self.feed_1.follow(self.user)
        self.assertFalse(SeenEntry.objects.filter(user=self.user, entry=self.entry_1_2).exists())
        response = self.auth_client.get(self.get_url(self.entry_1_2))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(SeenEntry.objects.filter(user=self.user, entry=self.entry_1_2).exists())


class EntryBookmarkTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = '/api/v1/rss/entries/bookmark/'
        cls.feed_1 = RSSFeedFactory()
        cls.feed_2 = RSSFeedFactory()

        cls.entry_1_1 = EntryFactory(feed=cls.feed_1)
        cls.entry_1_2 = EntryFactory(feed=cls.feed_1)
        cls.entry_2_1 = EntryFactory(feed=cls.feed_2)
        cls.entry_2_2 = EntryFactory(feed=cls.feed_2)

        cls.user = UserFactory()
        cls.auth_client = APIClient()
        cls.auth_client.force_login(cls.user)

    def test_bookmark_400(self):
        response = self.auth_client.patch(self.url)  # data is required
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.auth_client.patch(self.url, {'entry_id': uuid4()})  # invalid data
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_bookmark_400(self):
        response = self.auth_client.delete(self.url)  # data is required
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.auth_client.delete(self.url, {'entry_id': uuid4()})  # invalid data
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bookmark(self):
        response = self.auth_client.patch(self.url, {'entry_id': self.entry_2_1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.content)
        self.assertTrue(BookmarkedEntry.objects.filter(entry=self.entry_2_1, user=self.user).exists())
        # test duplicate request
        response = self.auth_client.patch(self.url, {'entry_id': self.entry_2_1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(BookmarkedEntry.objects.filter(entry=self.entry_2_1, user=self.user).count(), 1)

    def test_remove_bookmark(self):
        self.entry_2_1.add_bookmark(self.user)
        self.assertEqual(BookmarkedEntry.objects.filter(entry=self.entry_2_1, user=self.user).count(), 1)
        response = self.auth_client.delete(self.url, {'entry_id': self.entry_2_1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.content)
        self.assertEqual(BookmarkedEntry.objects.filter(entry=self.entry_2_1, user=self.user).count(), 0)


class EntryFavouriteTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = '/api/v1/rss/entries/favourite/'
        cls.feed_1 = RSSFeedFactory()

        cls.entry_1_1 = EntryFactory(feed=cls.feed_1)
        cls.entry_1_2 = EntryFactory(feed=cls.feed_1)

        cls.user = UserFactory()
        cls.auth_client = APIClient()
        cls.auth_client.force_login(cls.user)

    def test_favourite_400(self):
        response = self.auth_client.patch(self.url)  # data is required
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.auth_client.patch(self.url, {'entry_id': uuid4()})  # invalid data
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_favourite_400(self):
        response = self.auth_client.delete(self.url)  # data is required
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.auth_client.delete(self.url, {'entry_id': uuid4()})  # invalid data
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_favourite(self):
        response = self.auth_client.patch(self.url, {'entry_id': self.entry_1_1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.content)
        self.assertTrue(FavouritedEntry.objects.filter(entry=self.entry_1_1, user=self.user).exists())
        # test duplicate request
        response = self.auth_client.patch(self.url, {'entry_id': self.entry_1_1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(FavouritedEntry.objects.filter(entry=self.entry_1_1, user=self.user).count(), 1)

    def test_remove_favourite(self):
        self.entry_1_1.add_favourite(self.user)
        self.assertEqual(FavouritedEntry.objects.filter(entry=self.entry_1_1, user=self.user).count(), 1)
        response = self.auth_client.delete(self.url, {'entry_id': self.entry_1_1.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.content)
        self.assertEqual(FavouritedEntry.objects.filter(entry=self.entry_1_1, user=self.user).count(), 0)


class CommentEntryCreateTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = '/api/v1/rss/entry-comments/'
        cls.feed_1 = RSSFeedFactory()
        cls.entry_1_1 = EntryFactory(feed=cls.feed_1)

        cls.user = UserFactory()
        cls.auth_client = APIClient()
        cls.auth_client.force_login(cls.user)

    def test_status_401(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_body_field_is_required(self):
        response = self.auth_client.post(self.url, {'entry_id': self.entry_1_1.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_entry_id_is_required(self):
        response = self.auth_client.post(self.url, {'body': 'test'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_comment(self):
        response = self.auth_client.post(self.url, {'entry_id': self.entry_1_1.id, 'body': 'test'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(EntryComment.objects.filter(user=self.user, entry=self.entry_1_1).exists())

    def test_schema(self):
        response = self.auth_client.post(self.url, {'entry_id': self.entry_1_1.id, 'body': 'test'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        schema_validator = Validator(entry_comment_schema)
        self.assertTrue(schema_validator.validate(json.loads(response.content)), msg=schema_validator.errors)


class CommentEntryListTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = '/api/v1/rss/entry-comments/'
        cls.feed_1 = RSSFeedFactory()

        cls.entry_1 = EntryFactory(feed=cls.feed_1)
        cls.entry_2 = EntryFactory(feed=cls.feed_1)

        cls.comment = EntryCommentFactory(entry=cls.entry_1)

        cls.user = UserFactory()
        cls.auth_client = APIClient()
        cls.auth_client.force_login(cls.user)

    def test_status_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_schema(self):
        response = self.auth_client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        schema_validator = Validator(entry_comment_list_schema)
        self.assertTrue(schema_validator.validate(json.loads(response.content)), msg=schema_validator.errors)

    def test_entry_id_filter(self):
        response = self.auth_client.get(f'{self.url}?entry_id={self.entry_1.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], EntryComment.objects.filter(entry=self.entry_1).count())

        response = self.auth_client.get(f'{self.url}?entry_id={self.entry_2.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], EntryComment.objects.filter(entry=self.entry_2).count())


class TestCreateRSSFeed(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = '/api/v1/rss/feeds/'

        cls.user = UserFactory()
        cls.auth_client = APIClient()
        cls.auth_client.force_login(cls.user)

    def test_status_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @mock.patch('apps.rss.services.RSSFeedService._parse_feed_url', FakerRssFeedParse.valid_parser)
    def test_create(self):
        response = self.auth_client.post(self.url, {'feed_url': 'https://simpleisbetterthancomplex.com/feed.xml'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RSSFeed.objects.all().count(), 1)
        self.assertEqual(Entry.objects.all().count(), 1)

    @mock.patch('apps.rss.services.RSSFeedService._parse_feed_url', FakerRssFeedParse.valid_parser)
    def test_schema(self):
        response = self.auth_client.post(self.url, {'feed_url': 'https://simpleisbetterthancomplex.com/feed.xml'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        schema_validator = Validator(feed_schema_after_create)
        self.assertTrue(schema_validator.validate(json.loads(response.content)), msg=schema_validator.errors)
        self.assertIsNotNone(response.data['rss_feed'])

    @mock.patch('apps.rss.services.RSSFeedService._parse_feed_url', FakerRssFeedParse.invalid_parser_response_json)
    def test_invalid_content_type(self):
        response = self.auth_client.post(self.url, {'feed_url': 'https://google.com/'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        schema_validator = Validator(feed_schema_after_create)
        self.assertTrue(schema_validator.validate(json.loads(response.content)), msg=schema_validator.errors)
        self.assertFalse(response.data['rss_feed'])

    @mock.patch('apps.rss.services.RSSFeedService._parse_feed_url', FakerRssFeedParse.invalid_parser_response_404)
    def test_invalid_response(self):
        response = self.auth_client.post(self.url, {'feed_url': 'https://google.com/'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        schema_validator = Validator(feed_schema_after_create)
        self.assertTrue(schema_validator.validate(json.loads(response.content)), msg=schema_validator.errors)
        self.assertFalse(response.data['rss_feed'])


class TestUpdateRSSFeed(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.rss_feed = RSSFeedFactory(next_check=timezone.now() - timedelta(hours=1), is_active=True, last_status=200)

    @mock.patch('apps.rss.services.RSSFeedService._parse_feed_url', FakerRssFeedParse.valid_parser)
    def test_update_successfully(self):
        # create new entry if process run successfully
        update_feeds()
        self.assertEqual(Entry.objects.filter(feed=self.rss_feed).count(), 1)

    @mock.patch('apps.rss.services.RSSFeedService._parse_feed_url', FakerRssFeedParse.invalid_parser_response_404)
    def test_update_encounter_404(self):
        update_feeds()
        self.assertEqual(Entry.objects.filter(feed=self.rss_feed).count(), 0)
        self.rss_feed.refresh_from_db()
        self.assertEqual(self.rss_feed.last_status, 404)

    @mock.patch('apps.rss.services.RSSFeedService._parse_feed_url', FakerRssFeedParse.invalid_parser_response_404)
    @mock.patch('apps.rss.models.RSSFeed.ERROR_LIMIT', FakeLimitError.FAKE_ERROR_LIMIT)
    def test_deactivate(self):
        self.rss_feed.number_of_errors = 1
        self.rss_feed.save()
        update_feeds()
        self.rss_feed.refresh_from_db()
        self.assertEqual(self.rss_feed.is_active, False)
