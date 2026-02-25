import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from photographers.models import Photographer
from photos.models import Photo, UserFavorite

User = get_user_model()

PHOTOS_URL = "/api/photos"
FAVORITES_URL = "/api/favorites"

SAMPLE_SRC = {
    "original": "https://images.pexels.com/photos/1/photo.jpeg",
    "large2x": "https://images.pexels.com/photos/1/photo.jpeg?dpr=2",
    "large": "https://images.pexels.com/photos/1/photo.jpeg?h=650",
    "medium": "https://images.pexels.com/photos/1/photo.jpeg?h=350",
    "small": "https://images.pexels.com/photos/1/photo.jpeg?h=130",
    "portrait": "https://images.pexels.com/photos/1/photo.jpeg?h=1200",
    "landscape": "https://images.pexels.com/photos/1/photo.jpeg?h=627",
    "tiny": "https://images.pexels.com/photos/1/photo.jpeg?h=200",
}


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------
class TestPhotographerModel:
    def test_create(self, photographer):
        assert photographer.name == "Jane Doe"
        assert photographer.id == 1001

    def test_str(self, photographer):
        assert str(photographer) == "Jane Doe"


class TestPhotoModel:
    def test_create(self, photo):
        assert photo.width == 3888
        assert photo.height == 5184
        assert photo.photographer_id == 1001
        assert photo.src["original"].startswith("https://")

    def test_str(self, photo):
        assert "9001" in str(photo)
        assert "Jane Doe" in str(photo)

    def test_photographer_fk_cascade(self, photo):
        Photographer.objects.filter(id=photo.photographer_id).delete()
        assert not Photo.objects.filter(id=photo.id).exists()


class TestUserFavoriteModel:
    def test_create(self, user, photo):
        fav = UserFavorite.objects.create(user=user, photo=photo)
        assert fav.user == user
        assert fav.photo == photo
        assert fav.created_at is not None

    def test_unique_constraint(self, user, photo):
        UserFavorite.objects.create(user=user, photo=photo)
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            UserFavorite.objects.create(user=user, photo=photo)

    def test_str(self, user, photo):
        fav = UserFavorite.objects.create(user=user, photo=photo)
        assert str(user.email) in str(fav)


# ---------------------------------------------------------------------------
# Photo list endpoint
# ---------------------------------------------------------------------------
class TestPhotoList:
    def test_public_access(self, api_client, photo):
        resp = api_client.get(PHOTOS_URL)
        assert resp.status_code == status.HTTP_200_OK
        results = resp.json()["results"]
        assert len(results) == 1
        assert results[0]["id"] == photo.id

    def test_pagination(self, api_client, photographer, db):
        for i in range(25):
            Photo.objects.create(
                id=8000 + i,
                photographer=photographer,
                width=800, height=600,
                url=f"https://www.pexels.com/photo/p-{8000 + i}/",
                src=SAMPLE_SRC,
            )
        resp = api_client.get(PHOTOS_URL)
        data = resp.json()
        assert data["count"] == 25
        assert len(data["results"]) == 20
        assert data["next"] is not None

    def test_search_by_alt(self, api_client, photo, photo_b):
        resp = api_client.get(PHOTOS_URL, {"search": "landscape"})
        results = resp.json()["results"]
        assert len(results) == 1
        assert results[0]["id"] == photo.id

    def test_filter_by_photographer(self, api_client, photo, photo_b):
        resp = api_client.get(PHOTOS_URL, {"photographer_id": photo.photographer_id})
        results = resp.json()["results"]
        assert all(r["photographer_id"] == photo.photographer_id for r in results)

    def test_filter_by_avg_color(self, api_client, photo, photo_b):
        resp = api_client.get(PHOTOS_URL, {"avg_color": "#333831"})
        results = resp.json()["results"]
        assert len(results) == 1
        assert results[0]["id"] == photo.id

    def test_filter_width_range(self, api_client, photo, photo_b):
        resp = api_client.get(PHOTOS_URL, {"width_min": 3000, "width_max": 4000})
        results = resp.json()["results"]
        assert all(3000 <= r["width"] <= 4000 for r in results)

    def test_filter_height_range(self, api_client, photo, photo_b):
        resp = api_client.get(PHOTOS_URL, {"height_min": 5000})
        results = resp.json()["results"]
        assert len(results) == 1
        assert results[0]["id"] == photo.id

    def test_ordering_by_width(self, api_client, photo, photo_b):
        resp = api_client.get(PHOTOS_URL, {"ordering": "width"})
        results = resp.json()["results"]
        assert results[0]["width"] <= results[1]["width"]

    def test_list_includes_photographer_name(self, api_client, photo):
        resp = api_client.get(PHOTOS_URL)
        assert resp.json()["results"][0]["photographer_name"] == "Jane Doe"


# ---------------------------------------------------------------------------
# Photo detail endpoint
# ---------------------------------------------------------------------------
class TestPhotoDetail:
    def test_public_access(self, api_client, photo):
        resp = api_client.get(f"{PHOTOS_URL}/{photo.id}")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["id"] == photo.id
        assert data["photographer"]["name"] == "Jane Doe"
        assert data["src"]["original"].startswith("https://")

    def test_not_found(self, api_client, db):
        resp = api_client.get(f"{PHOTOS_URL}/999999")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# Photo create (admin only)
# ---------------------------------------------------------------------------
class TestPhotoCreate:
    def _payload(self, photographer):
        return {
            "id": 5001,
            "photographer_id": photographer.id,
            "width": 1920,
            "height": 1080,
            "url": "https://www.pexels.com/photo/new-5001/",
            "alt": "New photo",
            "avg_color": "#AABBCC",
            "src": SAMPLE_SRC,
        }

    def test_admin_can_create(self, admin_client, photographer):
        resp = admin_client.post(PHOTOS_URL, self._payload(photographer), format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert Photo.objects.filter(id=5001).exists()

    def test_regular_user_forbidden(self, auth_client, photographer):
        resp = auth_client.post(PHOTOS_URL, self._payload(photographer), format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_anonymous_unauthorized(self, api_client, photographer):
        resp = api_client.post(PHOTOS_URL, self._payload(photographer), format="json")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_required_fields(self, admin_client, db):
        resp = admin_client.post(PHOTOS_URL, {"id": 5002}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_rejects_nonexistent_photographer_id(self, admin_client, db):
        payload = {
            "id": 5013,
            "photographer_id": 999999,
            "width": 800,
            "height": 600,
            "url": "https://www.pexels.com/photo/new-5013/",
            "src": SAMPLE_SRC,
        }
        resp = admin_client.post(PHOTOS_URL, payload, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Photo update (admin only)
# ---------------------------------------------------------------------------
class TestPhotoUpdate:
    def test_admin_can_update(self, admin_client, photo):
        resp = admin_client.patch(
            f"{PHOTOS_URL}/{photo.id}",
            {"alt": "Updated description"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        photo.refresh_from_db()
        assert photo.alt == "Updated description"

    def test_admin_partial_update_multiple_fields(self, admin_client, photo):
        resp = admin_client.patch(
            f"{PHOTOS_URL}/{photo.id}",
            {"width": 1000, "height": 2000, "alt": "Multi-field update"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        photo.refresh_from_db()
        assert photo.width == 1000
        assert photo.height == 2000
        assert photo.alt == "Multi-field update"

    def test_regular_user_forbidden(self, auth_client, photo):
        resp = auth_client.patch(
            f"{PHOTOS_URL}/{photo.id}",
            {"alt": "Hacked"},
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_anonymous_unauthorized(self, api_client, photo):
        resp = api_client.patch(
            f"{PHOTOS_URL}/{photo.id}",
            {"alt": "Hacked"},
            format="json",
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# Photo delete (admin only)
# ---------------------------------------------------------------------------
class TestPhotoDelete:
    def test_admin_can_delete(self, admin_client, photo):
        resp = admin_client.delete(f"{PHOTOS_URL}/{photo.id}")
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not Photo.objects.filter(id=photo.id).exists()

    def test_regular_user_forbidden(self, auth_client, photo):
        resp = auth_client.delete(f"{PHOTOS_URL}/{photo.id}")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_anonymous_unauthorized(self, api_client, photo):
        resp = api_client.delete(f"{PHOTOS_URL}/{photo.id}")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_nonexistent(self, admin_client, db):
        resp = admin_client.delete(f"{PHOTOS_URL}/999999")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# Favorites list
# ---------------------------------------------------------------------------
class TestFavoriteList:
    def test_authenticated_empty(self, auth_client):
        resp = auth_client.get(FAVORITES_URL)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["results"] == []

    def test_authenticated_with_favorites(self, auth_client, user, photo, photo_b):
        UserFavorite.objects.create(user=user, photo=photo)
        UserFavorite.objects.create(user=user, photo=photo_b)
        resp = auth_client.get(FAVORITES_URL)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()["results"]) == 2

    def test_returns_only_own_favorites(self, user, photo, photo_b):
        other_user = User.objects.create_user(email="other@example.com", password="strongpass123")
        UserFavorite.objects.create(user=user, photo=photo)
        UserFavorite.objects.create(user=other_user, photo=photo_b)

        client = APIClient()
        client.force_authenticate(user=user)
        resp = client.get(FAVORITES_URL)
        results = resp.json()["results"]
        assert len(results) == 1
        assert results[0]["photo"]["id"] == photo.id

    def test_unauthenticated(self, api_client, db):
        resp = api_client.get(FAVORITES_URL)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_favorite_includes_photo_data(self, auth_client, user, photo):
        UserFavorite.objects.create(user=user, photo=photo)
        resp = auth_client.get(FAVORITES_URL)
        fav = resp.json()["results"][0]
        assert fav["photo"]["id"] == photo.id
        assert fav["photo"]["photographer_name"] == "Jane Doe"
        assert "created_at" in fav


# ---------------------------------------------------------------------------
# Favorite toggle (add / remove)
# ---------------------------------------------------------------------------
class TestFavoriteToggle:
    def test_add_favorite(self, auth_client, photo):
        resp = auth_client.post(f"{FAVORITES_URL}/{photo.id}")
        assert resp.status_code == status.HTTP_201_CREATED
        assert UserFavorite.objects.filter(photo=photo).exists()

    def test_add_duplicate_returns_conflict(self, auth_client, user, photo):
        UserFavorite.objects.create(user=user, photo=photo)
        resp = auth_client.post(f"{FAVORITES_URL}/{photo.id}")
        assert resp.status_code == status.HTTP_409_CONFLICT

    def test_add_nonexistent_photo(self, auth_client, db):
        resp = auth_client.post(f"{FAVORITES_URL}/999999")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_remove_favorite(self, auth_client, user, photo):
        UserFavorite.objects.create(user=user, photo=photo)
        resp = auth_client.delete(f"{FAVORITES_URL}/{photo.id}")
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not UserFavorite.objects.filter(user=user, photo=photo).exists()

    def test_remove_nonexistent_favorite(self, auth_client, photo):
        resp = auth_client.delete(f"{FAVORITES_URL}/{photo.id}")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_unauthenticated_add(self, api_client, photo):
        resp = api_client.post(f"{FAVORITES_URL}/{photo.id}")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_remove(self, api_client, photo):
        resp = api_client.delete(f"{FAVORITES_URL}/{photo.id}")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_different_users_independent(self, user, photo):
        other_user = User.objects.create_user(email="other@example.com", password="strongpass123")
        UserFavorite.objects.create(user=user, photo=photo)

        client = APIClient()
        client.force_authenticate(user=other_user)
        resp = client.delete(f"{FAVORITES_URL}/{photo.id}")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert UserFavorite.objects.filter(user=user, photo=photo).exists()


# ---------------------------------------------------------------------------
# Management command: ingest_photos
# ---------------------------------------------------------------------------
class TestIngestPhotosCommand:
    def test_ingest_creates_photographers_and_photos(self, db, tmp_path):
        import json
        data = [
            {
                "id": "100",
                "width": "800",
                "height": "600",
                "url": "https://www.pexels.com/photo/test-100/",
                "photographer": "Test Photographer",
                "photographer_url": "https://www.pexels.com/@test",
                "photographer_id": "50",
                "avg_color": "#FFFFFF",
                "src.original": "https://images.pexels.com/100.jpeg",
                "src.large2x": "",
                "src.large": "",
                "src.medium": "",
                "src.small": "",
                "src.portrait": "",
                "src.landscape": "",
                "src.tiny": "",
                "alt": "Test image",
            }
        ]
        json_file = tmp_path / "photos.json"
        json_file.write_text(json.dumps(data))

        from django.core.management import call_command
        call_command("ingest_photos", path=str(json_file))

        assert Photographer.objects.filter(id=50).exists()
        assert Photographer.objects.get(id=50).name == "Test Photographer"
        assert Photo.objects.filter(id=100).exists()
        photo = Photo.objects.get(id=100)
        assert photo.width == 800
        assert photo.alt == "Test image"
        assert photo.src["original"] == "https://images.pexels.com/100.jpeg"

    def test_ingest_is_idempotent(self, db, tmp_path):
        import json
        data = [
            {
                "id": "200",
                "width": "1920",
                "height": "1080",
                "url": "https://www.pexels.com/photo/test-200/",
                "photographer": "Idem Potent",
                "photographer_url": "https://www.pexels.com/@idem",
                "photographer_id": "60",
                "avg_color": "#000000",
                "src.original": "https://images.pexels.com/200.jpeg",
                "src.large2x": "",
                "src.large": "",
                "src.medium": "",
                "src.small": "",
                "src.portrait": "",
                "src.landscape": "",
                "src.tiny": "",
                "alt": "Idempotent test",
            }
        ]
        json_file = tmp_path / "photos.json"
        json_file.write_text(json.dumps(data))

        from django.core.management import call_command
        call_command("ingest_photos", path=str(json_file))
        call_command("ingest_photos", path=str(json_file))

        assert Photographer.objects.filter(id=60).count() == 1
        assert Photo.objects.filter(id=200).count() == 1
