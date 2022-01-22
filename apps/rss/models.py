import textwrap
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.validators import URLValidator
from django.db import models
from django.utils import timezone

from helper.model import BaseModel

User = get_user_model()


class ActiveRSSFeedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class RSSFeed(BaseModel):
    title = models.CharField(max_length=150, help_text="Title of the feed")
    feed_url = models.TextField(validators=[URLValidator()], unique=True, help_text="Link of the feed")
    description = models.TextField(help_text="Description of the feed")
    last_update = models.DateTimeField(blank=True, null=True, help_text="Last time the feed says it changed", )
    last_checked = models.DateTimeField(blank=True, null=True, help_text="Last time we checked the feed")
    next_check = models.DateTimeField(blank=True, null=True, help_text="Next time we need to update posts of feed")
    last_status = models.IntegerField(null=True, blank=True, help_text="Status code of last request")
    number_of_errors = models.IntegerField(default=0, help_text="Number of errors that have been occurred when updating posts")
    followers = models.ManyToManyField(
        to=User, related_name="feeds", through="RSSFeedFollower", help_text="Users who have followed RSS Feed")
    is_active = models.BooleanField(
        default=True, db_index=True, help_text="A feed will become inactive when a permanent error occurs"
    )
    objects = models.Manager()
    active_objects = ActiveRSSFeedManager()

    class Meta:
        ordering = ("-last_update", "-last_checked")
        verbose_name = "RSS Feed"
        verbose_name_plural = "RSS Feeds"

    def __str__(self):
        return f"{self.title} - {self.feed_url}"

    @classmethod
    def calculate_next_check(cls):
        return timezone.now() + timedelta(hours=1)

    def is_followed_by_user(self, user) -> bool:
        return self.followers.filter(id=user.id).exists()

    def unseen_entries_count_for_user(self, user) -> int:
        return self.entries.count() - self.entries.filter(seenentry__user_id=user.id).count()

    def follow(self, user):
        if not self.is_followed_by_user(user):
            self.followers.add(user)

    def unfollow(self, user):
        if self.is_followed_by_user(user):
            self.followers.remove(user)


class RSSFeedFollower(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    feed = models.ForeignKey(RSSFeed, on_delete=models.CASCADE)

    class Meta:
        ordering = ("-create_time",)
        verbose_name = "RSS Feed follower"
        verbose_name_plural = "RSS Feed followers"

    def __str__(self):
        return f"{self.user} {self.feed}"


class Entry(BaseModel):
    """
    Entries of feeds (Posts of feeds/Items of feeds)
    """
    feed = models.ForeignKey(RSSFeed, on_delete=models.CASCADE, related_name="entries")
    title = models.CharField(max_length=150, help_text="Title of the feed")
    url = models.TextField(null=True, blank=True, validators=[URLValidator()], help_text="URL for the HTML for this entry", )
    guid = models.TextField(null=True, blank=True, help_text="GUID for the entry, according to the feed")
    content = models.TextField(blank=True, help_text="description of entry")
    publish_date = models.DateTimeField(null=True, blank=True, help_text="when this entry says it was published", db_index=True)
    seen_users = models.ManyToManyField(
        to=User, related_name="seen_entries", through="SeenEntry", help_text="Users who have seen the entry"
    )
    favourite_users = models.ManyToManyField(
        to=User, related_name="favorited_entries", through="FavouritedEntry", help_text="Users who have favourited the entry"
    )
    bookmark_users = models.ManyToManyField(
        to=User, related_name="bookmarked_entries", through="BookmarkedEntry", help_text="Users who have bookmarked the entry"
    )

    class Meta:
        ordering = ("-publish_date", "-create_time")
        verbose_name = "Entry"
        verbose_name_plural = "Entries"

    def __str__(self):
        return f"{self.title} - {self.url}"

    def seen(self, user):
        if not self.seen_users.filter(id=user.id):
            self.seen_users.add(user)

    def add_bookmark(self, user):
        if not self.bookmark_users.filter(id=user.id):
            self.bookmark_users.add(user)

    def add_favourite(self, user):
        if not self.favourite_users.filter(id=user.id):
            self.favourite_users.add(user)

    def remove_bookmark(self, user):
        if self.bookmark_users.filter(id=user.id):
            self.bookmark_users.remove(user)

    def remove_favourite(self, user):
        if self.favourite_users.filter(id=user.id):
            self.favourite_users.remove(user)


class SeenEntry(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)

    class Meta:
        ordering = ("-create_time",)
        verbose_name = "Seen entry"
        verbose_name_plural = "Seen entries"

    def __str__(self):
        return f"{self.user} {self.entry}"


class FavouritedEntry(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)

    class Meta:
        ordering = ("-create_time",)
        verbose_name = "Favourited entry"
        verbose_name_plural = "Favourited entries"

    def __str__(self):
        return f"{self.user} {self.entry}"


class BookmarkedEntry(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)

    class Meta:
        ordering = ("-create_time",)
        verbose_name = "Bookmarked entry"
        verbose_name_plural = "Bookmarked entries"

    def __str__(self):
        return f"{self.user} {self.entry}"


class EntryComment(BaseModel):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="entry_comments", null=True, blank=True)
    body = models.TextField()

    class Meta:
        ordering = ("-create_time",)
        verbose_name = "Entry comment"
        verbose_name_plural = "Entry comments"

    def __str__(self):
        return f"{self.user}: {textwrap.shorten(self.body, width=25, placeholder='...')}"
