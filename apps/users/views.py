import os
from datetime import timedelta

import requests
from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.views import TokenRefreshView

from .models import (
    AdminAction,
    DashboardStats,
    EmailVerification,
    SocialAccount,
    SystemSettings,
    Token,
    User,
)
from .serializers import (
    AdminActionSerializer,
    AdminUserSerializer,
    DashboardStatsSerializer,
    EmailVerificationRequestSerializer,
    SystemSettingsSerializer,
    TokenSerializer,
    UserSerializer,
)
from .utils.email_token import confirm_email_token, generate_email_token
from .utils.send_email import send_verification_email

NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')


# 이메일 인증
class RequestEmailVerificationView(generics.GenericAPIView):
    serializer_class = EmailVerificationRequestSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        if User.objects.filter(email=email, email_verified=True).exists():
            return Response({"error": "이메일 중복"}, status=400)

        # 이전 인증 요청 만료 처리
        EmailVerification.objects.filter(email=email, is_used=False).update(
            expires_at=timezone.now()
        )
        token_code = generate_email_token(email)
        expires_at = timezone.now() + timedelta(hours=1)
        EmailVerification.objects.create(
            email=email, code=token_code, expires_at=expires_at
        )

        try:
            send_verification_email(email, token_code)
        except Exception:
            return Response({"error": "메일 발송 오류"}, status=500)

        return Response(
            {"message": "이메일 인증 메일 발송 완료 [1시간 유효]"}, status=200
        )

    # 사용자가 이메일 인증 요청
    # RequestEmailVerificationView에서 이메일 입력 후 POST.
    # DB에 EmailVerification 레코드 생성 (code, expires_at, is_used=False).
    # send_verification_email가 호출돼서 메일 발송.
    # 사용자가 메일에서 링크 클릭
    # 링크에는 token(여기서는 code) 포함.
    # ConfirmEmailView에서 GET으로 token 받음.
    # confirm_email_token(token) 호출 → 유효하면 이메일 반환.
    # 반환되면 Response로 “이메일 확인 완료” 메시지 전달.
    # 메일 링크 클릭 → ConfirmEmailView GET → 토큰 확인 → 이메일 인증 완료 구조임.


class ConfirmEmailView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        token_code = request.data.get("token") or request.GET.get("token")
        if not token_code:
            return Response({"error": "토큰 누락"}, 400)

        email = confirm_email_token(token_code)
        if not email:
            return Response({"error": "유효하지 않거나 만료된 토큰"}, 400)

        ev = EmailVerification.objects.filter(
            code=token_code, is_used=False, expires_at__gt=timezone.now()
        ).first()
        if ev:
            ev.is_used = True
            ev.save()

        try:
            user = User.objects.get(email=email)
            user.email_verified = True
            user.save()
            return Response({"verified": True}, 200)
        except User.DoesNotExist:
            return Response(
                {"error": "회원 없음", "error_status": "user_not_found"}, 400
            )

        # return Response({"message": "이메일 확인 완료"}, 200)


# 회원가입 / 로그인 / 로그아웃
class SignUpView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        token_code = request.data.get("token")
        if not token_code:
            return Response({"error": "인증 토큰 필요"}, 400)

        email = confirm_email_token(token_code)
        if not email:
            return Response({"error": "유효하지 않거나 만료된 토큰"}, 400)

        if User.objects.filter(email=email).exists():
            return Response({"error": "이메일 중복"}, 400)

        data = request.data.copy()
        data["email"] = email
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save(email_verified=True)
        EmailVerification.objects.filter(code=token_code).update(
            is_used=True, user=user
        )

        return Response({"message": "회원가입 완료"}, 201)


class LoginView(generics.GenericAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "이메일/비밀번호 오류"}, 400)

        if not check_password(password, user.password):
            return Response({"error": "이메일/비밀번호 오류"}, 400)
        if not user.email_verified:
            return Response({"error": "이메일 인증 필요"}, 401)

        refresh = RefreshToken.for_user(user)
        Token.objects.create(
            user=user,
            access_jwt=str(refresh.access_token),
            refresh_jwt=str(refresh),
            access_expires_at=timezone.now() + timedelta(minutes=5),
            refresh_expires_at=timezone.now() + timedelta(days=7),
        )

        return Response(
            {"access": str(refresh.access_token), "refresh": str(refresh)}, 200
        )


class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"logoutSuccess": False, "error": "refresh 필요"}, 400)

        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            pass

        t = Token.objects.filter(refresh_jwt=refresh_token, revoked=False).first()
        if t:
            t.revoked = True
            t.save()

        return Response({"logoutSuccess": True}, 200)


# 마이페이지 / 프로필 / 비밀번호 변경 / 회원 탈퇴
class UserProfileView(generics.GenericAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        data = request.data.copy()
        new_password = data.pop("password", None)

        if new_password:
            user.password = make_password(new_password)
            user.save()

        serializer = self.get_serializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response = {"update": True}
        if new_password:
            response["message"] = "프로필 및 비밀번호 업데이트 완료"
        else:
            response["user"] = serializer.data
        return Response(response)

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        user.deleted_at = timezone.now()
        user.is_active = False
        user.save()
        return Response({"message": "회원 탈퇴 처리 완료"}, 200)


# 토큰 관리
class TokenListView(generics.ListAPIView):
    serializer_class = TokenSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            Token.objects.all().order_by("-created_at")
            if getattr(user, "is_staff", False)
            else Token.objects.filter(user=user).order_by("-created_at")
        )


# 토큰 리프레쉬
from typing import Any, Tuple


class CustomTokenRefreshView(TokenRefreshView):
    permission_classes: Tuple[Any, ...] = (AllowAny,)


class TokenRevokeView(generics.GenericAPIView):
    permission_classes = (IsAdminUser,)

    def post(self, request, *args, **kwargs):
        token_id = request.data.get("token_id")
        if not token_id:
            return Response({"error": "token_id 필요"}, 400)

        try:
            t = Token.objects.get(id=token_id)
            t.revoked = True
            t.save()
            return Response({"message": "토큰 무효화 완료"}, 200)
        except Token.DoesNotExist:
            return Response({"error": "토큰 없음"}, 404)


# 네이버 로그인
# 추후 구글,카카오 구현 할 것
class NaverLoginView(generics.GenericAPIView):
    permission_classes = permissions.AllowAny

    def post(self, request, *args, **kwargs):
        code = request.data.get("code")
        state = request.data.get("state")
        if not code or not state:
            return Response({"error": "code/state 누락"}, 400)

        NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
        NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

        if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
            return Response({"error": "서버 환경변수 미설정"}, 500)

        token_url = "https://nid.naver.com/oauth2.0/token"
        token_params = {
            "grant_type": "authorization_code",
            "client_id": NAVER_CLIENT_ID,
            "client_secret": NAVER_CLIENT_SECRET,
            "code": code,
            "state": state,
        }

        try:
            token_res = requests.get(token_url, params=token_params, timeout=5)
            token_res.raise_for_status()
            token_data = token_res.json()
        except requests.RequestException as e:
            return Response({"error": "토큰 요청 실패", "detail": str(e)}, 400)

        access_token = token_data.get("access_token")
        if not access_token:
            return Response({"error": "토큰 요청 실패", "detail": token_data}, 400)

        profile_url = "https://openapi.naver.com/v1/nid/me"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            profile_res = requests.get(profile_url, headers=headers, timeout=5)
            profile_res.raise_for_status()
            profile_data = profile_res.json()
        except requests.RequestException as e:
            return Response({"error": "프로필 요청 실패", "detail": str(e)}, 400)

        if profile_data.get("resultcode") != "00":
            return Response(
                {"error": "네이버 프로필 요청 실패", "detail": profile_data}, 400
            )

        naver_user = profile_data["response"]
        email = naver_user.get("email")
        nickname = naver_user.get("nickname")
        provider_user_id = naver_user.get("id")

        user, _ = User.objects.get_or_create(
            email=email,
            defaults={"nickname": nickname, "email_verified": True, "password": "!"},
        )
        SocialAccount.objects.get_or_create(
            user=user, provider="naver", provider_user_id=provider_user_id
        )

        refresh = RefreshToken.for_user(user)
        Token.objects.create(
            user=user,
            access_jwt=str(refresh.access_token),
            refresh_jwt=str(refresh),
            access_expires_at=timezone.now() + timedelta(minutes=5),
            refresh_expires_at=timezone.now() + timedelta(days=7),
        )

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "email": user.email,
                "nickname": user.nickname,
            },
            200,
        )


# 어드민 기능
class AdminUserListView(generics.ListAPIView):
    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.all().order_by("-created_at")


class AdminUserStatusUpdateView(generics.UpdateAPIView):
    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.all()
    lookup_field = "pk"

    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        reason = serializer.validated_data.get("action_reason", "")
        action_type = ""
        if "is_active" in serializer.validated_data:
            action_type = (
                "RESTORE" if serializer.validated_data["is_active"] else "SUSPEND"
            )
        elif (
            "deleted_at" in serializer.validated_data
            and serializer.validated_data["deleted_at"]
        ):
            action_type = "DELETE"
        else:
            action_type = "RESTORE"

        if action_type:
            AdminAction.objects.create(
                admin_id=request.user.id,
                target_user_id=user.id,
                action_type=action_type,
                reason=reason,
            )

        return Response({"message": f"유저 상태 변경 완료 ({action_type})"})


class AdminActionCreateView(generics.CreateAPIView):
    queryset = AdminAction.objects.all()
    serializer_class = AdminActionSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        user_id = self.request.data.get("user_id")
        action_type = self.request.data.get("action_type")
        reason = self.request.data.get("reason", "")

        target_user = get_object_or_404(User, id=user_id)

        if action_type == "SUSPEND":
            target_user.is_active = False
            target_user.save()
        elif action_type == "RESTORE":
            target_user.is_active = True
            target_user.save()

        serializer.save(
            user=target_user,
            admin=self.request.user,
            action_type=action_type,
            reason=reason,
            created_at=timezone.now(),
        )

        def create(self, request, *args, **kwargs):
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"error": serializer.errors, "error_status": "invalid_data"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class AdminActionListView(generics.ListAPIView):
    serializer_class = AdminActionSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = AdminAction.objects.all().order_by("-created_at")
        # 선택적으로 admin_id나 target_user_id 필터링 가능
        admin_id = self.request.query_params.get("admin_id")
        target_id = self.request.query_params.get("target_user_id")
        if admin_id:
            queryset = queryset.filter(admin_id=admin_id)
        if target_id:
            queryset = queryset.filter(target_user_id=target_id)
        return queryset


# Dashboard 통계 조회 / 업데이트
class DashboardStatsListView(generics.ListAPIView):
    serializer_class = DashboardStatsSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return DashboardStats.objects.all().order_by("-stat_date")

    @staticmethod
    def update_daily_stats():
        today = timezone.localdate()
        total_users = User.objects.filter(deleted_at__isnull=True).count()
        # total_diaries와 api_calls는 실제 모델이나 API 호출 기록 필요
        total_diaries = 0
        api_calls = 0

        stat, created = DashboardStats.objects.get_or_create(stat_date=today)
        stat.total_users = total_users
        stat.total_diaries = total_diaries
        stat.api_calls = api_calls
        stat.save()


# 시스템 설정
class SystemSettingsListView(generics.ListAPIView):
    serializer_class = SystemSettingsSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return SystemSettings.objects.all().order_by("key")


class SystemSettingsDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = SystemSettingsSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = SystemSettings.objects.all()
