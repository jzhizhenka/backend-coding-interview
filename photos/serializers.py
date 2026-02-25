from rest_framework import serializers

from photographers.models import Photographer
from photographers.serializers import PhotographerSerializer

from .models import Photo, UserFavorite


class PhotoSerializer(serializers.ModelSerializer):
    photographer = PhotographerSerializer(read_only=True)
    photographer_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Photo
        fields = (
            "id",
            "photographer",
            "photographer_id",
            "width",
            "height",
            "url",
            "alt",
            "avg_color",
            "src",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def validate_photographer_id(self, value):
        if not Photographer.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                f"Photographer {value} does not exist."
            )
        return value


class PhotoListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views — avoids nested photographer object."""

    photographer_name = serializers.CharField(source="photographer.name", read_only=True)

    class Meta:
        model = Photo
        fields = (
            "id",
            "photographer_id",
            "photographer_name",
            "width",
            "height",
            "url",
            "alt",
            "avg_color",
            "src",
        )


class UserFavoriteSerializer(serializers.ModelSerializer):
    photo = PhotoListSerializer(read_only=True)

    class Meta:
        model = UserFavorite
        fields = ("photo", "created_at")
