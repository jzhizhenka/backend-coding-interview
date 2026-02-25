from django.db import models


class Photographer(models.Model):
    id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    profile_url = models.URLField(max_length=2048, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "photographers"

    def __str__(self):
        return self.name
