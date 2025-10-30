from rest_framework import serializers
from .models import OutfitRecommendation


class OutfitRecommendSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutfitRecommendation
        fields = ["id", "rec_1", "rec_2", "rec_3", "explanation", "image_url", "created_at"]