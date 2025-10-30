from django.shortcuts import render
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.response import Response

from .models import AiChatLogs
from .utils import ask_gpt


class AiChatViewSet(viewsets.ViewSet):

    def create(self, request):
        user = request.user if request.user.is_authenticated else None
        question = request.data.get("question")

        if not question:
            return Response(
                {"error": "AI 대화 실패"}, status=status.HTTP_400_BAD_REQUEST
            )

        answer = ask_gpt(question)

        chat_log = AiChatLogs.objects.create(
            user=user,
            user_question=question,
            ai_answer=answer,
            context={"source": "gpt"},
            created_at=timezone.now(),
        )

        return Response(
            {"question": question, "answer": answer, "id": chat_log.id},
            status=status.HTTP_201_CREATED,
        )
