from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class OutfitRecommendation(models.Model):
    """날씨 기반 코디 추천 결과"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recommendations"
    )

    #  chatbot 앱의 모델을 ForeignKey로 참조
    ai_model_setting = models.ForeignKey(
        "chatbot.AiModelSettings",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="outfit_recommendations",
    )

    weather_data_id = models.IntegerField(null=True, blank=True)
    rec_1 = models.TextField()  # 필수
    rec_2 = models.TextField(blank=True, null=True)
    rec_3 = models.TextField(blank=True, null=True)
    explanation = models.TextField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "outfit_recommendation"

    def __str__(self):
        return f"Recommend #{self.id} ({self.user})"
