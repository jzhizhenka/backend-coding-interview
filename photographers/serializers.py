from rest_framework import serializers

from .models import Photographer


class PhotographerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photographer
        fields = ("id", "name", "profile_url", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")
