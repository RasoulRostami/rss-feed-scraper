from rest_framework.routers import SimpleRouter

from .views import RSSFeedView, EntryView, EntryCommentView

app_name = 'rss'

router = SimpleRouter()
router.register('entry-comments', EntryCommentView, basename='entry-comments')
router.register('feeds', RSSFeedView, basename='feeds')
router.register('entries', EntryView, basename='entries')

urls = [
]
urlpatterns = urls + router.urls
