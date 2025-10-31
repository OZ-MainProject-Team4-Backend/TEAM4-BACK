from django.urls import path

from .views import (
    AdminActionListView,
    AdminUserListView,
    AdminUserStatusUpdateView,
    ConfirmEmailView,
    CustomTokenRefreshView,
    DashboardStatsListView,
    GoogleLoginView,
    LoginView,
    LogoutView,
    NaverLoginView,
    RequestEmailVerificationView,
    SignUpView,
    SystemSettingsDetailView,
    SystemSettingsListView,
    TokenListView,
    TokenRevokeView,
    UserProfileView,
)

urlpatterns = [
    # 이메일 인증
    path(
        "email/request/",
        RequestEmailVerificationView.as_view(),
        name="request_email_verification",
    ),
    path("email/confirm/", ConfirmEmailView.as_view(), name="confirm_email"),
    # 회원가입 / 로그인 / 로그아웃
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # 마이페이지 / 유저 정보 / 비밀번호 변경 / 회원 탈퇴
    path("profile/", UserProfileView.as_view(), name="user_profile"),
    # 토큰 관리
    path("tokens/", TokenListView.as_view(), name="token_list"),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path("tokens/revoke/", TokenRevokeView.as_view(), name="token_revoke"),
    # 소셜 로그인
    path("login/naver/", NaverLoginView.as_view(), name="naver_login"),
    path("login/google/", GoogleLoginView.as_view(), name="google_login"),
    # 어드민 기능
    path("admin/users/", AdminUserListView.as_view(), name="admin_user_list"),
    path(
        "admin/users/<int:pk>/status/",
        AdminUserStatusUpdateView.as_view(),
        name="admin_user_status_update",
    ),
    path("admin/actions/", AdminActionListView.as_view(), name="admin_action_list"),
    path(
        "api/users/admin/actions/create/",
        AdminActionListView.as_view(),
        name="admin_create_action_list",
    ),
    path(
        "admin/dashboard-stats/",
        DashboardStatsListView.as_view(),
        name="dashboard_stats_list",
    ),
    path(
        "admin/system-settings/",
        SystemSettingsListView.as_view(),
        name="system_settings_list",
    ),
    path(
        "admin/system-settings/<int:pk>/",
        SystemSettingsDetailView.as_view(),
        name="system_settings_detail",
    ),
]
