from django.conf import settings
from django.core.mail import EmailMessage


def send_verification_email(email, token):
    subject = "이메일 인증을 완료해주세요."
    verify_url = f"http://localhost:8000/api/auth/verify-email?token={token}"

    message = f"""
    안녕하세요!
    아래의 링크를 클릭하면 이메일 인증이 완료가됩니다! 

    {verify_url}

    인증 링크는 1시간 후 만료됩니다.

    """

    email_message = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
    email_message.send(fail_silently=False)
