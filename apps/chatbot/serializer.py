from rest_framework import serializers

from apps.chatbot.models import AiChatLogs


class AiChatLogReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiChatLogs
        fields = [
            "id",
            "session_id",
            "user_question",
            "ai_answer",
            "context",
            'created_at',
        ]


class SessionSummarySerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    last_message_at = serializers.DateTimeField()
    message_count = serializers.IntegerField()
    last_question = serializers.CharField(allow_blank=True)
    last_answer = serializers.CharField(allow_blank=True)
