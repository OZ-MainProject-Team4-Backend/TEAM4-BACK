from apps.locations.models import Location, FavoriteLocation
from rest_framework import serializers


class LocationSerializer(serializers.ModelSerializer):
    """위치 정보 직렬화"""
    class Meta:
        model = Location
        fields = ["id", "city", "district", "latitude", "longitude"]

class FavoriteLocationSerializer(serializers.ModelSerializer):
    """즐겨찾기 위치 직렬화"""
    location = LocationSerializer(read_only=True)

    class Meta:
        model = FavoriteLocation
        fields = ["id", "alias", "is_default", "location", "created_at"]

