from django.contrib import admin

from .models import Photo, UserFavorite


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "photographer", "width", "height", "avg_color", "created_at")
    list_filter = ("photographer",)
    search_fields = ("alt",)
    ordering = ("-id",)


@admin.register(UserFavorite)
class UserFavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "photo", "created_at")
    list_filter = ("user",)
    ordering = ("-created_at",)
