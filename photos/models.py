from django.conf import settings
from django.db import models
from django.contrib.postgres.indexes import GinIndex


class Photo(models.Model):
    id = models.BigIntegerField(primary_key=True)
    photographer = models.ForeignKey(
        "photographers.Photographer",
        on_delete=models.CASCADE,
        related_name="photos",
    )
    width = models.IntegerField()
    height = models.IntegerField()
    url = models.URLField(max_length=2048)
    alt = models.TextField(blank=True, default="")
    avg_color = models.CharField(max_length=7, blank=True, default="")
    src = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "photos"
        indexes = [
            models.Index(fields=["photographer"], name="idx_photos_photographer"),
            models.Index(fields=["avg_color"], name="idx_photos_avg_color"),
            GinIndex(fields=["src"], name="idx_photos_src_gin"),
        ]

    def __str__(self):
        return f"Photo {self.id} by {self.photographer.name}"


class UserFavorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    photo = models.ForeignKey(
        Photo,
        on_delete=models.CASCADE,
        related_name="favorited_by",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_favorites"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "photo"],
                name="unique_user_photo_favorite",
            ),
        ]

    def __str__(self):
        return f"{self.user} → Photo {self.photo_id}"
