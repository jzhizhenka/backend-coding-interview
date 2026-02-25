from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Photo, UserFavorite
from .permissions import IsAdminOrReadOnly
from .serializers import PhotoSerializer, PhotoListSerializer, UserFavoriteSerializer
from .filters import PhotoFilter


class PhotoListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_class = PhotoFilter
    search_fields = ("alt",)
    ordering_fields = ("id", "width", "height", "created_at")
    ordering = ("-id",)

    def get_queryset(self):
        return Photo.objects.select_related("photographer").all()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PhotoListSerializer
        return PhotoSerializer


class PhotoDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAdminOrReadOnly,)
    serializer_class = PhotoSerializer

    def get_queryset(self):
        return Photo.objects.select_related("photographer").all()


class FavoriteListView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserFavoriteSerializer

    def get_queryset(self):
        return (
            UserFavorite.objects
            .filter(user=self.request.user)
            .select_related("photo__photographer")
            .order_by("-created_at")
        )


class FavoriteToggleView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, photo_id):
        photo = get_object_or_404(Photo, pk=photo_id)
        _, created = UserFavorite.objects.get_or_create(
            user=request.user, photo=photo,
        )
        if not created:
            return Response(
                {"detail": "Photo already in favorites."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response({"detail": "Photo added to favorites."}, status=status.HTTP_201_CREATED)

    def delete(self, request, photo_id):
        deleted, _ = UserFavorite.objects.filter(
            user=request.user, photo_id=photo_id,
        ).delete()
        if not deleted:
            return Response(
                {"detail": "Photo not in favorites."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
