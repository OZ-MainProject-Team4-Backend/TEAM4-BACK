from django.db import models
from django.utils import timezone

from apps.locations.models import Location


class SoftDeleteMixin(models.Model):
    """Soft Delete Mixin — 실제 삭제 대신 deleted_at 기록"""

    deleted_at = models.DateTimeField(blank=True, null=True)  # 삭제 시각

    class Meta:
        abstract = True  # 독립 테이블로 생성되지 않음

    def delete(self, using=None, keep_parents=False):
        """Soft delete 동작"""
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    def restore(self):
        """삭제 복구"""
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])


class WeatherData(SoftDeleteMixin):
    """
    지역별 날씨 데이터 저장 테이블
    - OpenWeather API 사용
    - 위치(Location)와 1:N 관계
    """

    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="weather_data",
    )  # 위치 FK → Locations.id

    provider = models.CharField(
        max_length=50,
        default="OpenWeather",
    )  # 데이터 제공자 (OpenWeather)

    weather_type = models.CharField(
        max_length=20,
        choices=[("current", "Current"), ("forecast", "Forecast")],
        default="current",
    )  # 데이터 유형 (current / forecast)

    base_time = models.DateTimeField()  # API 기준 시각 (데이터 생성 기준)
    valid_time = models.DateTimeField()  # 실제 유효 시각 (데이터 적용 시간)

    # 기상 수치
    temperature = models.DecimalField(max_digits=5, decimal_places=2)  # 기온(°C)
    feels_like = models.DecimalField(max_digits=5, decimal_places=2)  # 체감온도(°C)
    humidity = models.PositiveSmallIntegerField()  # 습도(%) - 정수형
    rain_probability = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )  # 강수확률(%)
    rain_volume = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )  # 강수량(mm)
    wind_speed = models.DecimalField(max_digits=5, decimal_places=2)  # 풍속(m/s)
    icon = models.CharField(max_length=10, blank=True, null=True)  # 날씨 아이콘 코드
    condition = models.CharField(max_length=100)  # 날씨 상태 (예: 맑음, 비, 눈)

    raw_payload = models.JSONField(blank=True, null=True)  # 원본 API 응답 JSON (백업용)
    created_at = models.DateTimeField(auto_now_add=True)  # 데이터 생성 시각

    class Meta:
        db_table = "weather_data"
        verbose_name = "Weather Data"
        verbose_name_plural = "Weather Data"
        constraints = [
            # 동일 위치 + 제공자 + 데이터유형 + 유효시간 중복 방지
            models.UniqueConstraint(
                fields=["location", "provider", "weather_type", "valid_time"],
                name="uq_location_provider_type_validtime",
            ),
        ]
        indexes = [
            models.Index(fields=["location"]),
            models.Index(fields=["valid_time"]),
            models.Index(fields=["weather_type"]),
        ]

    def __str__(self):
        """예시: '서울특별시 강남구 - Cloudy (18.3°C)'"""
        return f"{self.location.city} {self.location.district} - {self.condition} ({self.temperature}°C)"


class WeatherDailySummary(SoftDeleteMixin):
    """
    일별 날씨 요약 데이터
    - 특정 날짜에 대한 최저/최고 온도, 습도, 주요 상태 기록
    - 다이어리, 추천, 통계 기능에서 참조
    """

    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="weather_daily_summary",
    )  # 위치 FK → Locations.id
    date = models.DateField()  # 날짜 (YYYY-MM-DD)

    # 기상 수치
    temperature_min = models.DecimalField(
        max_digits=5, decimal_places=2
    )  # 최저 기온(°C)
    temperature_max = models.DecimalField(
        max_digits=5, decimal_places=2
    )  # 최고 기온(°C)
    humidity_min = models.PositiveSmallIntegerField()  # 최저 습도(%)
    humidity_max = models.PositiveSmallIntegerField()  # 최고 습도(%)
    dominant_condition = models.CharField(
        max_length=100
    )  # 하루 중 가장 많이 나타난 상태 (예: Cloudy)
    provider = models.CharField(
        max_length=50, default="OpenWeather"
    )  # 데이터 제공자(OpenWeather)

    created_at = models.DateTimeField(auto_now_add=True)  # 통계 생성 시각

    class Meta:
        db_table = "weather_daily_summary"
        verbose_name = "Weather Daily Summary"
        verbose_name_plural = "Weather Daily Summaries"
        constraints = [
            # 동일 위치 + 날짜 중복 방지
            models.UniqueConstraint(
                fields=["location", "date"], name="uq_location_date"
            ),
        ]
        indexes = [
            models.Index(fields=["location"]),
            models.Index(fields=["date"]),
        ]

    def __str__(self):
        """예시: '서울특별시 강남구 (2025-10-29)'"""
        return f"{self.location.city} {self.location.district} ({self.date})"
