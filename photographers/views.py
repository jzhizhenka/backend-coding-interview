from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend

from photos.permissions import IsAdminOrReadOnly

from .models import Photographer
from .serializers import PhotographerSerializer


class PhotographerListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsAdminOrReadOnly,)
    serializer_class = PhotographerSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("name",)
    ordering_fields = ("id", "name", "created_at")
    ordering = ("name",)

    def get_queryset(self):
        return Photographer.objects.all()


class PhotographerDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAdminOrReadOnly,)
    serializer_class = PhotographerSerializer

    def get_queryset(self):
        return Photographer.objects.all()
