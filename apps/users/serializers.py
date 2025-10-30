# serializers.py
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from rest_framework import serializers

from .models import (
    AdminAction,
    DashboardStats,
    EmailVerification,
    SocialAccount,
    SystemSettings,
    Token,
    User,
)


# ---------------------------
# User
# ---------------------------
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_null=True)
    is_active = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "password",
            "name",
            "nickname",
            "phone",
            "gender",
            "email_verified",
            "deleted_at",
            "is_staff",
            "is_superuser",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = (
            "email_verified",
            "created_at",
            "updated_at",
            "is_staff",
            "is_superuser",
        )

    def get_is_active(self, obj):
        return obj.is_active

    def validate_email(self, value):
        request = self.context.get("request")
        if request and request.method == "POST":
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError("이미 사용중인 이메일입니다.")
        return value

    def validate_password(self, value):
        if value is None or value == "":
            return value
        if len(value) < 8:
            raise serializers.ValidationError("비밀번호는 최소 8자 이상이어야 합니다.")
        if " " in value:
            raise serializers.ValidationError("비밀번호에 공백을 포함할 수 없습니다.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User.objects.create(**validated_data)
        if password:
            user.password = make_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password:
            instance.password = make_password(password)
            instance.save()
        return super().update(instance, validated_data)


# ---------------------------
# EmailVerification
# ---------------------------
class EmailVerificationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), allow_null=True, required=False
    )

    class Meta:
        model = EmailVerification
        fields = ["id", "user", "email", "code", "is_used", "expires_at", "created_at"]
        read_only_fields = ["id", "created_at"]


class EmailVerificationRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


# ---------------------------
# SocialAccount
# ---------------------------
class SocialAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialAccount
        fields = ["id", "user", "provider", "provider_user_id", "connected_at"]
        read_only_fields = ["connected_at"]


# ---------------------------
# Token
# ---------------------------
class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = [
            "id",
            "user",
            "access_jwt",
            "refresh_jwt",
            "access_expires_at",
            "refresh_expires_at",
            "revoked",
            "created_at",
        ]
        read_only_fields = ["created_at"]


# ---------------------------
# Admin
# ---------------------------
class AdminUserSerializer(serializers.ModelSerializer):
    action_reason = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "name",
            "nickname",
            "phone",
            "gender",
            "is_staff",
            "email_verified",
            "deleted_at",
            "action_reason",
        ]
        read_only_fields = ["email"]


class AdminActionSerializer(serializers.ModelSerializer):
    admin_email = serializers.EmailField(source="admin.email", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = AdminAction
        fields = [
            "id",
            "admin_email",
            "user_email",
            "action_type",
            "reason",
            "created_at",
        ]
        read_only_fields = ["created_at"]


# ---------------------------
# Dashboard / System
# ---------------------------
class DashboardStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardStats
        fields = [
            "id",
            "stat_date",
            "total_users",
            "total_diaries",
            "api_calls",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class SystemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSettings
        fields = ["id", "key", "value", "description", "updated_at"]
        read_only_fields = ["updated_at"]


# ---------------------------
# Password reset helpers
# ---------------------------
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                "새 비밀번호와 확인 비밀번호가 일치하지 않습니다."
            )
        if len(data["new_password"]) < 8:
            raise serializers.ValidationError("비밀번호는 최소 8자 이상이어야 합니다.")
        if " " in data["new_password"]:
            raise serializers.ValidationError("비밀번호에 공백을 포함할 수 없습니다.")
        return data
