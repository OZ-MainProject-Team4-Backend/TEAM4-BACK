from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class SoftDeleteMixin(models.Model):
    """Soft Delete Mixin"""

    deleted_at = models.DateTimeField(blank=True, null=True)  # 삭제 시각 (Soft Delete)

    class Meta:
        abstract = True  # DB 테이블 생성 안 함

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()  # 실제 삭제 대신 삭제 시각 기록
        self.save()

    def restore(self):
        self.deleted_at = None  # 삭제 복구
        self.save()


class Location(models.Model):
    """
    지역 및 좌표 정보 테이블
    - 도시, 구, 동 단위까지 지역 정보를 저장
    - 위도(latitude), 경도(longitude)는 UNIQUE
    """

    city = models.CharField(max_length=50)  # 도시명 (예: 서울특별시)
    district = models.CharField(max_length=50)  # 구 단위 (예: 강남구)
    subdistrict = models.CharField(
        max_length=50, blank=True, null=True
    )  # 동 단위 (예: 역삼동)
    latitude = models.DecimalField(
        max_digits=10, decimal_places=7
    )  # 위도 (예: 37.5665)
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7
    )  # 경도 (예: 126.9780)
    is_active = models.BooleanField(default=True)  # 활성화 여부
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 시각
    updated_at = models.DateTimeField(auto_now=True)  # 수정 시각

    class Meta:
        db_table = "locations"
        verbose_name = "위치"
        verbose_name_plural = "위치 목록"
        constraints = [
            models.UniqueConstraint(
                fields=["latitude", "longitude"],
                name="unique_latitude_longitude",
            ),
        ]
        indexes = [
            models.Index(fields=["city"]),
            models.Index(fields=["district"]),
            models.Index(fields=["latitude", "longitude"]),
        ]

    def __str__(self):
        parts = [self.city, self.district, self.subdistrict]
        return " ".join([p for p in parts if p])  # ex) 서울특별시 강남구 역삼동


class FavoriteLocation(SoftDeleteMixin):
    """
    사용자별 즐겨찾기 위치 관리 테이블
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorite_locations",  # 역참조: user.favorite_locations.all()
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="favorited_by",  # 역참조: location.favorite_by.all()
    )
    alias = models.CharField(
        max_length=100, blank=True, null=True
    )  # 별칭 (예: 집, 회사)
    is_default = models.BooleanField(default=False)  # 기본 위치 여부
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 시각
    updated_at = models.DateTimeField(auto_now=True)  # 수정 시각

    class Meta:
        db_table = "favorite_locations"
        verbose_name = "Favorite Location"
        verbose_name_plural = "Favorite Locations"
        constraints = [
            # 한 유저는 같은 위치를 중복 등록할 수 없음
            models.UniqueConstraint(
                fields=["user", "location"], name="uq_user_location"
            ),
            # 기본 위치는 유저당 하나만 가능
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_default=True),
                name="uq_user_default_location",
            ),
        ]

    def __str__(self):
        return f"{self.user.nickname} - {self.alias or self.location.city}"
