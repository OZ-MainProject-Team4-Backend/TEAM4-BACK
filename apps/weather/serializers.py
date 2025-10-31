from rest_framework import serializers

from .models import WeatherDailySummary, WeatherData


class WeatherDataSerializer(serializers.ModelSerializer):
    """현재 날씨 / 예보 데이터를 직렬화"""

    location_name = serializers.SerializerMethodField()  # 도시, 구 이름을 문자열로 반환

    class Meta:
        model = WeatherData
        fields = [
            "id",
            "location_name",
            "temperature",
            "feels_like",
            "humidity",
            "rain_probability",
            "rain_volume",
            "wind_speed",
            "condition",
            "icon",
            "weather_type",
            "valid_time",
            "provider",
        ]

    def get_location_name(self, obj):
        """도시 + 구 조합을 문자열로 반환"""
        return f"{obj.location.city} {obj.location.district}"


class WeatherDailySummarySerializer(serializers.ModelSerializer):
    """일별 요약 데이터를 직렬화"""

    location_name = serializers.SerializerMethodField()

    class Meta:
        model = WeatherDailySummary
        fields = [
            "id",
            "location_name",
            "date",
            "temperature_min",
            "temperature_max",
            "humidity_min",
            "humidity_max",
            "dominant_condition",
            "provider",
        ]

    def get_location_name(self, obj):
        return f"{obj.location.city} {obj.location.district}"
