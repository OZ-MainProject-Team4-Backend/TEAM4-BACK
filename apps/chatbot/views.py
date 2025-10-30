from django.shortcuts import render
from django.utils import timezone
from rest_framework import status, viewsets, permissions
from rest_framework.response import Response

from .models import AiChatLogs
from .serializer import SessionSummarySerializer, AiChatLogReadSerializer
from .utils import ask_gpt

from rest_framework.pagination import PageNumberPagination

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


class ChatPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 200

class SessionViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def _base_queryset(self, request):
        qs = AiChatLogs.objects.all()
        user = request.user if request.user.is_authenticated else None
        if user:
            qs = qs.filter(user=user)
        return qs

    def list(self, request):
        limit = int(request.query_params.get("limit", 20))

        qs = self._base_queryset(request)

        agg = (
            qs.values("session_id")
            .annotate(
                last_message_at = Max("created_at"),
                message_count = Count("id")
            )
            .order_by("-last_message_at")
        )[:limit]

        session_ids = [row["session_id"] for row in agg]
        last_logs = (
            AiChatLogs.objects.filter(session_id__in = session_ids)
            .order_by("session_id","-created_at")
            .distinct("session_id")
        )
        last_map = {str(x.session_id): x for x in last_logs}

        data = []
        for row in agg:
            sid = str(row["session_id"])
            last = last_map.get(sid)
            data.append({
                "session_id": row["session_id"],
                "last_message": last["last_message_at"],
                "message_count": row["message_count"],
                "last_question": (last.user_question if last else "") or "",
                "last_answer": (last.ai_answer if last else "") or "",
            })

            serializer = SessionSummarySerializer(data=data, many=True)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data, status = status.HTTP_200_OK)

    def retrieve(self, request, pk=None):

        paginator = ChatPagination()
        qs = (
            self._base_queryset(request)
            .filter(session_id=pk)
            .order_by("-created_at")
        )

        page = paginator.paginate_queryset(qs, request)
        ser = AiChatLogReadSerializer(page, many=True)
        return paginator.get_paginated_response(ser.data)