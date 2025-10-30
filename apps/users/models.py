import os

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .utils.send_email import send_verification_email


#유저입력창
class User(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=150, unique=True, null=False)
    password = models.CharField(max_length=255, null=False)
    name = models.CharField(max_length=100, blank=True, null=True)
    nickname = models.CharField(max_length=50, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)

    email_verified = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)

    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email

    def soft_delete(self):
        """Soft delete helper"""
        self.deleted_at = timezone.now()
        self.save()

    @property
    def is_active(self):
        return self.deleted_at is None


class EmailVerification(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="email_verifications",
        null=True,
        blank=True,
    )
    email = models.EmailField(max_length=150)
    code = models.CharField(max_length=100)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "email_verifications"
        verbose_name = "Email Verification"
        verbose_name_plural = "Email Verifications"

    def __str__(self):
        return f"{self.user.email} - {self.code}"

    def send_verification_email(self):
        try:
            send_verification_email(self.email, self.code)
        except Exception as e:
            print(f"Email send failed: {e}")


@receiver(post_save, sender=EmailVerification)
def email_verification_post_save(sender, instance, created, **kwargs):
    if created and not instance.is_used:
        instance.send_verification_email()


class SocialAccount(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.CharField(max_length=20)
    provider_user_id = models.CharField(max_length=200)
    connected_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "social_accounts"
        verbose_name = "Social Account"
        verbose_name_plural = "Social Accounts"
        unique_together = ("provider", "provider_user_id")

    def __str__(self):
        return f"{self.user.email} - {self.provider}"


class Token(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    access_jwt = models.CharField(
        max_length=500, blank=True, null=True
    )  # JWT 길이가 200을 넘을 수 있으므로 500으로 변경
    refresh_jwt = models.CharField(
        max_length=500, blank=True, null=True
    )  # JWT 길이가 200을 넘을 수 있으므로 500으로 변경
    access_expires_at = models.DateTimeField(blank=True, null=True)
    refresh_expires_at = models.DateTimeField(blank=True, null=True)
    revoked = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "tokens"
        verbose_name = "Token"
        verbose_name_plural = "Tokens"

    def __str__(self):
        return f"Token for {self.user.email}"


class AdminAction(models.Model):
    ACTION_CHOICES = [
        ("SUSPEND", "계정 정지"),
        ("RESTORE", "계정 복구"),
        ("WARNING", "경고"),
        ("DELETE", "삭제"),
        ("OTHER", "기타"),
    ]

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="admin_actions",
        verbose_name="관리자",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_actions",
        verbose_name="대상 유저",
    )
    action_type = models.CharField(
        max_length=20, choices=ACTION_CHOICES, verbose_name="조치 유형"
    )
    reason = models.TextField(blank=True, null=True, verbose_name="사유")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="조치 시각")

    class Meta:
        db_table = "admin_action_log"
        verbose_name = "관리자 조치 로그"
        verbose_name_plural = "관리자 조치 로그 목록"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_action_type_display()}] {self.user.email} by {self.admin.email}"


class DashboardStats(models.Model):
    stat_date = models.DateField()
    total_users = models.IntegerField(default=0)
    total_diaries = models.IntegerField(default=0)
    api_calls = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "dashboard_stats"


class SystemSettings(models.Model):
    key = models.CharField(max_length=150, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "system_settings"
        ordering = ["key"]

    def __str__(self):
        return f"{self.key} : {self.value}"
