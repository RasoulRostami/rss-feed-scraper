import django_filters

from .models import RSSFeed, RSSFeedFollower, Entry, BookmarkedEntry, FavouritedEntry, SeenEntry


class RSSFeedFilter(django_filters.FilterSet):
    is_followed = django_filters.BooleanFilter(method='get_is_followed')

    class Meta:
        model = RSSFeed
        fields = ('is_active', 'is_followed')

    def get_is_followed(self, queryset, name, value):
        return queryset.filter(id__in=RSSFeedFollower.objects.filter(user=self.request.user).values_list('feed_id', flat=True))


class EntryFilter(django_filters.FilterSet):
    is_bookmarked = django_filters.BooleanFilter(method='get_is_bookmarked')
    is_favourited = django_filters.BooleanFilter(method='get_is_favourited')
    is_seen = django_filters.BooleanFilter(method='get_is_seen')

    class Meta:
        model = Entry
        fields = ('is_bookmarked', 'is_favourited', 'is_seen', 'feed_id')

    def get_is_bookmarked(self, queryset, name, value):
        return queryset.filter(id__in=BookmarkedEntry.objects.filter(user=self.request.user).values_list('entry_id', flat=True))

    def get_is_favourited(self, queryset, name, value):
        return queryset.filter(id__in=FavouritedEntry.objects.filter(user=self.request.user).values_list('entry_id', flat=True))

    def get_is_seen(self, queryset, name, value):
        return queryset.filter(id__in=SeenEntry.objects.filter(user=self.request.user).values_list('entry_id', flat=True))
