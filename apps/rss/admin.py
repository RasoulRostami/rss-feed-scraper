from django.contrib.admin import register

from helper.admin import BaseAdminModel
from .models import *


@register(RSSFeed)
class RSSFeedAdmin(BaseAdminModel):
    list_display = ('title', 'feed_url')
    list_filter = ('is_active',)


@register(RSSFeedFollower)
class RSSFeedFollowerAdmin(BaseAdminModel):
    list_display = ('user', 'feed')


@register(Entry)
class EntryAdmin(BaseAdminModel):
    list_display = ('title', 'title', 'url')


@register(SeenEntry)
class SeenEntryAdmin(BaseAdminModel):
    list_display = ('user', 'entry')


@register(BookmarkedEntry)
class BookmarkedEntryAdmin(BaseAdminModel):
    list_display = ('user', 'entry')


@register(FavouritedEntry)
class FavouritedEntryAdmin(BaseAdminModel):
    list_display = ('user', 'entry')


@register(EntryComment)
class EntryCommentAdmin(BaseAdminModel):
    list_display = ('user', 'entry', 'body')
