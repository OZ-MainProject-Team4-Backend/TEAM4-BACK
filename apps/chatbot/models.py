import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import CheckConstraint, Q
from django.utils import timezone


class AiModelSettings(models.Model):
    id = models.AutoField(primary_key=True)  # Ai_model_settings_id
    # ERD 상에는 int 로 지정되어 있지만 자동 증가를 위해 AutoField로 지정함
    # 구조상 문제가 있을 시 에는 int 로 수정 가능 바로 피드백 해주세요 ~

    name = models.CharField(max_length=150)  # Ai모델 이름

    temperature_max = models.FloatField()  # 최고기온
    temperature_min = models.FloatField()  # 최저기온

    humidity_max = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )  # 최고습도
    humidity_min = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )  # 최저습도

    weather_condition = models.CharField(max_length=100, blank=True)  # 기상컨디션
    category_combo = models.CharField(max_length=255)  # 추천조합
    active = models.BooleanField(default=True)  # 활성화여부

    created_at = models.DateTimeField(default=timezone.now)  # 생성시각
    updated_at = models.DateTimeField(auto_now=True)  # 수정시각

    class Meta:
        db_table = "ai_model_setting"  # 실제 DB에 저장될 이름
        indexes = [
            models.Index(fields=["active"]),
            models.Index(fields=["weather_condition"]),
            models.Index(fields=["temperature_max", "temperature_min"]),
            models.Index(fields=["humidity_max", "humidity_min"]),
        ]  # 검색 속도 향상을 위한 인덱스 설정

        constraints = [
            CheckConstraint(
                check=Q(temperature_min__lte=models.F("temperature_max")),
                name="ck_temp_min_le_max",
            ),
            CheckConstraint(
                check=Q(humidity_min__lte=models.F("humidity_max")),
                name="ck_humidity_min_le_max",
            ),
        ]  # 무결성


class AiChatLogs(models.Model):
    id = models.AutoField(primary_key=True)  # Ai_chat_logs_id
    # ERD 상에는 int 로 지정되어 있지만 자동 증가를 위해 AutoField로 지정함
    # 구조상 문제가 있을 시 에는 int 로 수정 가능 바로 피드백 해주세요 ~

    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_chat_logs",
    )  # user_id FK

    ai_model_setting_id = models.ForeignKey(
        AiModelSettings,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_chat_logs",
    )  # Ai_model_settings_id FK

    session_id = models.CharField(
        max_length=200,
        default=uuid.uuid4,
        editable=False,
        db_index=True,
    )  # 대화 세션 식별자

    user_question = models.TextField()  # 사용자 질문
    ai_answer = models.TextField()  # ai 답변

    context = models.JSONField(default=dict)  # 추천시 사용된 정보

    created_at = models.DateTimeField(default=timezone.now)  # 기록 시각

    class Meta:
        db_table = "ai_chat_logs"  # 실제로 DB 에 저장될 이름
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["session_id", "created_at"]),
            models.Index(fields=["user_id", "created_at"]),
        ]  # 검색 최적화 인덱스

    def __str__(self):
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {self.user_question[:30]}..."
