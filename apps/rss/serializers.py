from rest_framework import serializers

from .models import RSSFeed, Entry, EntryComment
from ..account.serializers import UserReadOnlySerializer


class RSSFeedSerializer(serializers.ModelSerializer):
    number_of_followers = serializers.SerializerMethodField()
    is_followed = serializers.SerializerMethodField()
    number_of_unseen_entries = serializers.SerializerMethodField(allow_null=True)

    class Meta:
        model = RSSFeed
        fields = (
            'id',
            'title',
            'feed_url',
            'description',
            'last_update',
            'last_checked',
            'number_of_unseen_entries',
            'number_of_followers',
            'is_followed',
            'is_active',
        )
        read_only = True

    def get_number_of_followers(self, rss_feed):
        return rss_feed.followers.count()

    def get_is_followed(self, rss_feed):
        return rss_feed.is_followed_by_user(self.context['request'].user)

    def get_number_of_unseen_entries(self, rss_feed):
        if not rss_feed.is_followed_by_user(self.context['request'].user):
            return 0
        return rss_feed.unseen_entries_count_for_user(self.context['request'].user)


class RSSFeedCreateSerializer(serializers.Serializer):
    feed_url = serializers.URLField(required=True)
    message = serializers.CharField(read_only=True)
    rss_feed = RSSFeedSerializer(allow_null=True, required=False, read_only=True)


class RSSFeedFollowSerializer(serializers.Serializer):
    feed_id = serializers.PrimaryKeyRelatedField(queryset=RSSFeed.objects.all(), required=True, source='feed')


class EntrySerializer(serializers.ModelSerializer):
    is_bookmarked = serializers.SerializerMethodField()
    is_favourited = serializers.SerializerMethodField()

    class Meta:
        model = Entry
        fields = (
            'id',
            'feed',
            'title',
            'url',
            'guid',
            'content',
            'publish_date',
            'is_bookmarked',
            'is_favourited',
        )
        read_only = True

    def get_is_bookmarked(self, entry):
        return entry.bookmark_users.filter(id=self.context['request'].user.id).exists()

    def get_is_favourited(self, entry):
        return entry.favourite_users.filter(id=self.context['request'].user.id).exists()


class EntryBookmarkSerializer(serializers.Serializer):
    entry_id = serializers.PrimaryKeyRelatedField(queryset=Entry.objects.all(), required=True, source='entry')


class EntryFavouriteSerializer(serializers.Serializer):
    entry_id = serializers.PrimaryKeyRelatedField(queryset=Entry.objects.all(), required=True, source='entry')


class EntryCommentSerializer(serializers.ModelSerializer):
    entry_id = serializers.PrimaryKeyRelatedField(queryset=Entry.objects.all(), required=True, source='entry')
    user_id = serializers.HiddenField(default=serializers.CurrentUserDefault(), source='user', write_only=True)
    user = UserReadOnlySerializer(read_only=True)

    class Meta:
        model = EntryComment
        fields = (
            'id',
            'entry_id',
            'user_id',
            'body',
            'user',
        )
        extra_kwargs = {'user_id': {'read_only': True}}
