# TODO: زمان ایجاد فید جدید زمان ابدیت بعدیش رو بزار
'''
متدهای اماری داخل کلاس rss
تمام فیلدهای rss_serializer
rss filters and search
duplicate follow and duplicate seen, bookmark ... action
is_active
'''
import json
from uuid import uuid4

from cerberus import Validator
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.account.tests.factories import UserFactory
from .factories import RSSFeedFactory, EntryFactory
from .schemas import rss_feed_list_schema
from ..models import RSSFeed, RSSFeedFollower


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


class RSSFeedCreateTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = '/api/v1/rss/feeds/'
