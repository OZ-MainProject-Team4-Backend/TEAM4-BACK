from rest_framework.routers import DefaultRouter

from .views import AiChatViewSet, SessionViewSet

router = DefaultRouter()
router.register(r"send", AiChatViewSet, basename="send")
router.register(r"session", SessionViewSet, basename="session")

urlpatterns = router.urls
