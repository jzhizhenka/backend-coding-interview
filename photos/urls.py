from django.urls import path

from . import views

urlpatterns = [
    path("photos", views.PhotoListCreateView.as_view(), name="photo-list"),
    path("photos/<int:pk>", views.PhotoDetailView.as_view(), name="photo-detail"),
    path("favorites", views.FavoriteListView.as_view(), name="favorite-list"),
    path("favorites/<int:photo_id>", views.FavoriteToggleView.as_view(), name="favorite-toggle"),
]
