import json
from pathlib import Path

from django.core.management.base import BaseCommand

from photographers.models import Photographer
from photos.models import Photo

SRC_KEYS = (
    "original", "large2x", "large", "medium", "small",
    "portrait", "landscape", "tiny",
)


class Command(BaseCommand):
    help = "Ingest photo data from photos.json into the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=str(Path(__file__).resolve().parents[3] / "photos.json"),
            help="Path to photos.json file",
        )

    def handle(self, *args, **options):
        file_path = options["path"]
        with open(file_path) as f:
            data = json.load(f)

        photographers: dict[int, dict] = {}
        photos: list[dict] = []

        for row in data:
            pid = int(row["photographer_id"])
            if pid not in photographers:
                photographers[pid] = {
                    "id": pid,
                    "name": row["photographer"],
                    "profile_url": row.get("photographer_url", ""),
                }

            src = {key: row.get(f"src.{key}", "") for key in SRC_KEYS}
            photos.append({
                "id": int(row["id"]),
                "photographer_id": pid,
                "width": int(row["width"]),
                "height": int(row["height"]),
                "url": row["url"],
                "alt": row.get("alt", ""),
                "avg_color": row.get("avg_color", ""),
                "src": src,
            })

        photographer_objs = [Photographer(**p) for p in photographers.values()]
        Photographer.objects.bulk_create(
            photographer_objs,
            update_conflicts=True,
            update_fields=["name", "profile_url"],
            unique_fields=["id"],
        )
        self.stdout.write(f"Upserted {len(photographer_objs)} photographers")

        photo_objs = [Photo(**p) for p in photos]
        Photo.objects.bulk_create(
            photo_objs,
            update_conflicts=True,
            update_fields=["width", "height", "url", "alt", "avg_color", "src"],
            unique_fields=["id"],
        )
        self.stdout.write(self.style.SUCCESS(f"Upserted {len(photo_objs)} photos"))
