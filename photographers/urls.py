from django.urls import path

from . import views

urlpatterns = [
    path("photographers", views.PhotographerListCreateView.as_view(), name="photographer-list"),
    path("photographers/<int:pk>", views.PhotographerDetailView.as_view(), name="photographer-detail"),
]
