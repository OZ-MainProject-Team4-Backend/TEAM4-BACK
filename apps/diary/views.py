from rest_framework import generics

from apps.diary.serializers import DiarySerializer


class DiaryViewSet(generics.GenericAPIView):
    serializer_class = DiarySerializer


