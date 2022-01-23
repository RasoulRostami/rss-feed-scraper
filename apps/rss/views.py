from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.mixins import ListModelMixin, CreateModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_extensions.mixins import NestedViewSetMixin

from helper.drf import GetCustomSerializerClass
from .exceptions import InvalidFeedURL
from .filters import RSSFeedFilter, EntryFilter
from .models import RSSFeed, Entry, EntryComment
from .serializers import (
    RSSFeedCreateSerializer,
    RSSFeedSerializer,
    RSSFeedFollowSerializer,
    EntrySerializer,
    EntryBookmarkSerializer,
    EntryFavouriteSerializer,
    EntryCommentSerializer,
)
from .services import RSSFeedService, EntryService


class RSSFeedView(GetCustomSerializerClass, ListModelMixin, CreateModelMixin, GenericViewSet):
    queryset = RSSFeed.objects.all()
    serializer_class = RSSFeedSerializer
    create_serializer_class = RSSFeedCreateSerializer
    filter_backends = (SearchFilter, DjangoFilterBackend)
    search_fields = ('title', 'feed_url')
    filterset_class = RSSFeedFilter

    @swagger_auto_schema(request_body=RSSFeedCreateSerializer(), responses={status.HTTP_200_OK: RSSFeedCreateSerializer()})
    def create(self, request, *args, **kwargs):
        """
        ## If an RSS Feed is not exits user can create new one and follow it
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rss_service = RSSFeedService()
        try:
            rss_feed = rss_service.create(
                feed_url=serializer.validated_data['feed_url'],
                create_or_update_entries_function=EntryService().create_or_update
            )
            serializer = self.get_serializer({
                'feed_url': serializer.validated_data['feed_url'],
                'message': 'RSS Feed successfully was created',
                'rss_feed': rss_feed
            })
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except InvalidFeedURL:
            serializer = self.get_serializer({
                'feed_url': serializer.validated_data['feed_url'],
                'message': 'RSS Feed URL is invalid',
            })
            return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        methods=['patch', 'delete'], request_body=RSSFeedFollowSerializer(), responses={status.HTTP_200_OK: None}
    )
    @action(detail=False, methods=['patch', 'delete'], serializer_class=RSSFeedFollowSerializer)
    def follow(self, request, *args, **kwargs):
        """
        ## Follow / Unfollow RSS Feed
        - patch: **Follow** RSS Feed
        - delete: **Unfollow** RSS Feed
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        feed = serializer.validated_data['feed']
        if request.method == "PATCH":
            feed.follow(request.user)
        elif request.method == "DELETE":
            feed.unfollow(request.user)
        return Response(status=status.HTTP_200_OK)


class EntryView(NestedViewSetMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = Entry.objects.all()
    serializer_class = EntrySerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = EntryFilter

    def retrieve(self, request, *args, **kwargs):
        """
        ## If the current user has followed the feed of entry, entry is added to seen table after retrieve
        """
        entry = self.get_object()
        if entry.feed.is_followed_by_user(request.user):
            entry.seen(request.user)
        serializer = self.get_serializer(entry)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        methods=['patch', 'delete'], request_body=EntryBookmarkSerializer(), responses={status.HTTP_200_OK: None}
    )
    @action(detail=False, methods=['patch', 'delete'], serializer_class=EntryBookmarkSerializer)
    def bookmark(self, request, *args, **kwargs):
        """
        ## Add entry to bookmark / Remove entry from bookmark
        - patch: **Add bookmark**
        - delete: **Remove bookmark**
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entry = serializer.validated_data['entry']
        if request.method == "PATCH":
            entry.add_bookmark(request.user)
        elif request.method == "DELETE":
            entry.remove_bookmark(request.user)
        return Response(status=status.HTTP_200_OK)

    @swagger_auto_schema(
        methods=['patch', 'delete'], request_body=EntryFavouriteSerializer(), responses={status.HTTP_200_OK: None}
    )
    @action(detail=False, methods=['patch', 'delete'], serializer_class=EntryFavouriteSerializer)
    def favourite(self, request, *args, **kwargs):
        """
        ## Add entry to favourites / Remove entry from favourites
        - patch: **Add favourite**
        - delete: **Remove favourite**
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entry = serializer.validated_data['entry']
        if request.method == "PATCH":
            entry.add_favourite(request.user)
        elif request.method == "DELETE":
            entry.remove_favourite(request.user)
        return Response(status=status.HTTP_200_OK)


class EntryCommentView(ListModelMixin, CreateModelMixin, GenericViewSet):
    queryset = EntryComment.objects.all()
    serializer_class = EntryCommentSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('entry_id',)
