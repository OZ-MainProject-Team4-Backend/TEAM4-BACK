from django.db import models
from django.utils import timezone

from apps.locations.models import Location


class SoftDeleteMixin(models.Model):
    deleted_at = models.DateTimeField(blank=True, null=True)  # 삭제 시각

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """실제 삭제 대신 삭제 시각 기록"""
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        """삭제 복구"""
        self.deleted_at = None
        self.save()


class WeatherData(SoftDeleteMixin):
    """
    실시간 또는 단기예보 날씨 데이터
    - OpenWeather API에서 받아온 데이터
    - location FK로 지역 연결
    """

    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="weather_data",
    )
    temperature = models.DecimalField(max_digits=5, decimal_places=2)  # 현재 온도(°C)
    feels_like = models.DecimalField(max_digits=5, decimal_places=2)  # 체감 온도(°C)
    humidity = models.PositiveSmallIntegerField()  # 습도(%)
    wind_speed = models.DecimalField(max_digits=5, decimal_places=2)  # 풍속(m/s)
    rain_probability = models.PositiveSmallIntegerField(default=0)  # 강수 확률(%)
    condition = models.CharField(max_length=50)  # 날씨 상태 (예: Clear, Rain)
    icon = models.CharField(
        max_length=10, blank=True, null=True
    )  # OpenWeather 아이콘 코드
    fetched_at = models.DateTimeField(default=timezone.now)  # 수집 시각
    is_forecast = models.BooleanField(
        default=False
    )  # 예보 데이터 여부 (True=Forecast, False=Current)

    class Meta:
        db_table = "weather_data"
        verbose_name = "Weather Data"
        verbose_name_plural = "Weather Data"
        indexes = [
            models.Index(fields=["fetched_at"]),
            models.Index(fields=["location"]),
        ]

    def __str__(self):
        return f"{self.location.city} - {self.condition} ({self.temperature}°C)"


class WeatherDailySummary(SoftDeleteMixin):
    """
    하루 단위 날씨 요약 (과거 데이터)
    - 일기나 통계용으로 사용
    """

    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="weather_summaries",
    )
    date = models.DateField()  # 날짜
    temperature_min = models.DecimalField(max_digits=5, decimal_places=2)  # 최저 온도
    temperature_max = models.DecimalField(max_digits=5, decimal_places=2)  # 최고 온도
    humidity_min = models.PositiveSmallIntegerField()  # 최소 습도
    humidity_max = models.PositiveSmallIntegerField()  # 최대 습도
    dominant_condition = models.CharField(max_length=50)  # 대표 날씨 상태 (예: Cloudy)
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 시각

    class Meta:
        db_table = "weather_daily_summary"
        verbose_name = "Weather Daily Summary"
        verbose_name_plural = "Weather Daily Summaries"
        constraints = [
            models.UniqueConstraint(
                fields=["location", "date"], name="uq_location_date"
            ),
        ]
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["location"]),
        ]

    def __str__(self):
        return f"{self.location.city} ({self.date})"
