from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.diary.models import Diary
from apps.diary.serializers import DiaryDetailSerializer, DiaryListSerializer


class DiaryViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Diary.objects.filter(user=self.request.user, deleted_at__isnull=True)

    def list(self, request):
        year = request.query_params.get("year")
        month = request.query_params.get("month")
        diary_qs = self.get_queryset()

        if year and month:
            diary_qs = diary_qs.filter(date__year=year, date__month=month)

        if not diary_qs.exists():
            return Response(
                {"error": "존재하지 않습니다", "error_status": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = DiaryListSerializer(diary_qs, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        try:
            diary = self.get_queryset().get(pk=pk)
        except Diary.DoesNotExist:
            return Response(
                {"error": "존재하지 않습니다", "error_status": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = DiaryDetailSerializer(diary)
        return Response(serializer.data)
