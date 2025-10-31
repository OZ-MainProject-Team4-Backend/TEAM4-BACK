from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LocationSearchView, FavoriteLocationViewSet

router = DefaultRouter()
router.register(r"favorites", FavoriteLocationViewSet, basename="favorites")

urlpatterns = [
    path("search/", LocationSearchView.as_view(), name="location-search"),
    path("", include(router.urls)),
]
