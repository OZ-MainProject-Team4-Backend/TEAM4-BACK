from rest_framework import serializers
from ..users.serializers import UserSerializer
from ..weather.serializers import WeatherDataSerializer
from .models import Diary


class DiarySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    weather_data = WeatherDataSerializer(read_only=True)

    class Meta:
        model = Diary
        fields = [
            "id",
            "user",
            "date",
            "weather_data",
            "satisfaction",
            "title",
            "notes",
            "image_url",
            "created_at",
            "updated_at",
            "deleted_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "deleted_at"]