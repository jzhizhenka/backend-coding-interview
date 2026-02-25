from django.contrib import admin

from .models import Photographer


@admin.register(Photographer)
class PhotographerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)
    ordering = ("name",)
