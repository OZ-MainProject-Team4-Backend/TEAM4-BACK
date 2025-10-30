from django.conf import settings
from itsdangerous import (
    URLSafeTimedSerializer,  # URLSafeTimeSerializer -> URLSafeTimedSerializer 변경
)

serializer = URLSafeTimedSerializer(settings.SECRET_KEY)  # 클래스 이름 변경


def generate_email_token(email):
    return serializer.dumps(email, salt="email-confirm")


def confirm_email_token(token, expiration=3600):
    try:
        email = serializer.loads(token, salt="email-confirm", max_age=expiration)
        return email
    except Exception:
        return None
