from factory import fuzzy, django, Faker, SubFactory

from apps.account.tests.factories import UserFactory
from ..models import RSSFeed, Entry, EntryComment


class RSSFeedFactory(django.DjangoModelFactory):
    class Meta:
        model = RSSFeed

    title = Faker('name')
    feed_url = Faker('url')
    description = Faker('text')
    last_update = Faker('date_time')
    last_checked = Faker('date_time')
    next_check = Faker('date_time')
    last_status = fuzzy.FuzzyChoice([200, 400, 401, 403, 404, 500])
    number_of_errors = Faker('numerify')


class EntryFactory(django.DjangoModelFactory):
    class Meta:
        model = Entry

    feed = SubFactory(RSSFeedFactory)
    title = Faker('name')
    url = Faker('url')
    guid = Faker('url')
    content = Faker('text')
    publish_date = Faker('date_time')


class EntryCommentFactory(django.DjangoModelFactory):
    class Meta:
        model = EntryComment

    entry = SubFactory(EntryFactory)
    user = SubFactory(UserFactory)
    body = Faker('text')
