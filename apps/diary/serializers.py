from rest_framework import serializers

from ..weather.serializers import WeatherDataSerializer
from .models import Diary


class DiaryListSerializer(serializers.ModelSerializer):  # 목록조회
    class Meta:
        model = Diary
        fields = ["id", "date", "title"]


class DiaryDetailSerializer(serializers.ModelSerializer):  # 상세조회
    weather_data = WeatherDataSerializer(read_only=True)

    class Meta:
        model = Diary
        fields = [
            "id",
            "date",
            "title",
            "satisfaction",
            "notes",
            "image_url",
            "weather_data",
            "created_at",
            "updated_at",
        ]


class DiaryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diary
        fields = ["title", "satisfaction", "notes", "image_url", "weather_data"]

    def create(self, validated_data):
        user = self.context["request"].user
        return Diary.objects.create(user=user, **validated_data)
