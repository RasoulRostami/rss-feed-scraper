from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import RSSFeed
from .services import EntryService, RSSFeedService

User = get_user_model()


@shared_task
def update_feeds(*args, **kwargs):
    for feed in RSSFeed.objects.filter(next_check__lte=timezone.now()):
        rss_service = RSSFeedService()
        rss_service.update(feed, EntryService().create_or_update)
