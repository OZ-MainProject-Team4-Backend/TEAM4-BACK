from django.db import models
from django.conf import settings


User = settings.AUTH_USER_MODEL


class AIModelSettings(models.Model):
    """AI 추천 모델 설정 테이블"""
    name = models.CharField(max_length=150)
    temperature_min = models.FloatField()
    temperature_max = models.FloatField()
    humidity_min = models.IntegerField(null=True, blank=True)
    humidity_max = models.IntegerField(null=True, blank=True)
    weather_condition = models.CharField(max_length=100, blank=True, null=True)
    category_combo = models.CharField(max_length=255, blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_model_settings"

    def __str__(self):
        return f"{self.name}"


class OutfitRecommendation(models.Model):
    """날씨 기반 코디 추천 결과"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recommendations")
    model_setting_id = models.ForeignKey(AIModelSettings, on_delete=models.SET_NULL, null=True, blank=True)
    weather_data_id = models.IntegerField(null=True, blank=True)
    rec_1 = models.TextField() # 필수
    rec_2 = models.TextField(blank=True, null=True)
    rec_3 = models.TextField(blank=True, null=True)
    explanation = models.TextField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "outfit_recommendation"

    def __str__(self):
        return f"Recommend #{self.id} ({self.user})"