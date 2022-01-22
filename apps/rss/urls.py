from rest_framework.routers import SimpleRouter
from rest_framework_extensions.routers import ExtendedSimpleRouter

from .views import RSSFeedView, EntryView, EntryCommentView

app_name = 'rss'

nested_router = ExtendedSimpleRouter()

nested_router.register(
    'feeds',
    RSSFeedView,
    basename='feeds'
).register(
    'entries',
    EntryView,
    basename='entries',
    parents_query_lookups=['feed_id']
)

router = SimpleRouter()
router.register('entry-comments', EntryCommentView, basename='entry-comments')

urls = [
]
urlpatterns = urls + router.urls + nested_router.urls
