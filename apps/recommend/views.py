from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .serializers import OutfitRecommendSerializer
from .services.recommend_service import generate_outfit_recommend


class OutfitRecommendView(generics.GenericAPIView):
    """
    날씨 기반 코디 추천 뷰
    - 사용자 인증 필요
    - POST 요청 시 위도(latitude), 경도(longitude)를 받아 추천 생성
    """

    permission_classes = [IsAuthenticated]
    serializer_class = OutfitRecommendSerializer

    def post(self, request):
        latitude = request.data.get("latitude")
        longitude = request.data.get("longitude")
        user = request.user

        # 추천 생성
        reco = generate_outfit_recommend(user, latitude, longitude)

        serializer = self.get_serializer(reco)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
