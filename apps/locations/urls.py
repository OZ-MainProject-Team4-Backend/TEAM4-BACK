from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FavoriteLocationViewSet, LocationSearchView

router = DefaultRouter()
router.register(r"favorites", FavoriteLocationViewSet, basename="favorites")

urlpatterns = [
    path("search/", LocationSearchView.as_view(), name="location-search"),
    path("", include(router.urls)),
]
