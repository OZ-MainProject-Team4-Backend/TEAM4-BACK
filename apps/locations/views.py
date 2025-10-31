from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import FavoriteLocation, Location
from .serializers import FavoriteLocationSerializer, LocationSerializer


# 좌표 기반 지역 검색
class LocationSearchView(generics.GenericAPIView):
    """
    GET /api/location/search?lat=&lon=
    위도(lat), 경도(lon)를 쿼리로 받아 DB에서 해당 위치 조회
    city, district, latitude, longitude 반환
    """

    queryset = Location.objects.all()
    serializer_class = LocationSerializer

    def get(self, request, *args, **kwargs):
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")

        if not lat or not lon:
            return Response(
                {"error": "좌표 오류", "error_status": "invalid_coordinate"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            latitude = float(lat)
            longitude = float(lon)
        except ValueError:
            return Response(
                {
                    "error": "좌표 형식이 잘못되었습니다.",
                    "error_status": "invalid_coordinate",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        location = Location.objects.filter(
            latitude=latitude,
            longitude=longitude,
        ).first()

        if not location:
            return Response(
                {
                    "error": "해당 좌표에 대한 지역 정보가 없습니다.",
                    "error_status": "invalid_coordinate",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(location)
        return Response(serializer.data, status=status.HTTP_200_OK)


# 즐겨찾기 관리 CRUD
class FavoriteLocationViewSet(viewsets.ModelViewSet):
    """
    /api/location/favorites/
    GET: 즐겨찾기 목록 조회
    POST: 즐겨찾기 추가
    PATCH: 별칭 수정 / 기본 위치 설정
    DELETE: 즐겨찾기 삭제
    """

    queryset = FavoriteLocation.objects.select_related("location").all()
    serializer_class = FavoriteLocationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """현재 로그인한 사용자 데이터만 조회"""
        return FavoriteLocation.objects.filter(
            user=self.request.user, deleted_at__isnull=True
        ).select_related("location")

    def perform_create(self, serializer):
        """중복 등록 방지 + 기본위치 처리"""
        user = self.request.user
        location = serializer.validated_data.get("location")

        # 동일 위치 중복 방지
        if FavoriteLocation.objects.filter(
            user=user, location=location, deleted_at__isnull=True
        ).exists():
            return Response(
                {"error": "중복 등록", "error_status": "favorite_duplicate"},
                status=status.HTTP_409_CONFLICT,
            )

        serializer.save(user=user)

    def destroy(self, request, *args, **kwargs):
        """Soft Delete (deleted_at 기록)"""
        instance = self.get_object()
        instance.delete()
        return Response({"message": "삭제 완료"}, status=status.HTTP_204_NO_CONTENT)

    def partial_update(self, request, *args, **kwargs):
        """별칭 수정 or 기본 위치 설정"""
        instance = self.get_object()
        alias = request.data.get("alias")
        is_default = request.data.get("is_default")

        if alias:
            instance.alias = alias

        if is_default is not None:
            # 기존 기본 위치를 해제
            FavoriteLocation.objects.filter(user=request.user, is_default=True).update(
                is_default=False
            )
            instance.is_default = is_default

        instance.save()
        return Response({"message": "수정 완료"}, status=status.HTTP_200_OK)
