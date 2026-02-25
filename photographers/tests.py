import pytest
from rest_framework import status

from photographers.models import Photographer

PHOTOGRAPHERS_URL = "/api/photographers"


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------
class TestPhotographerList:
    def test_public_access(self, api_client, photographer):
        resp = api_client.get(PHOTOGRAPHERS_URL)
        assert resp.status_code == status.HTTP_200_OK
        results = resp.json()["results"]
        assert len(results) == 1
        assert results[0]["name"] == photographer.name

    def test_search_by_name(self, api_client, photographer, photographer_b):
        resp = api_client.get(PHOTOGRAPHERS_URL, {"search": "Jane"})
        results = resp.json()["results"]
        assert len(results) == 1
        assert results[0]["id"] == photographer.id

    def test_ordering_by_name(self, api_client, photographer, photographer_b):
        resp = api_client.get(PHOTOGRAPHERS_URL, {"ordering": "name"})
        results = resp.json()["results"]
        names = [r["name"] for r in results]
        assert names == sorted(names)


# ---------------------------------------------------------------------------
# Detail
# ---------------------------------------------------------------------------
class TestPhotographerDetail:
    def test_public_access(self, api_client, photographer):
        resp = api_client.get(f"{PHOTOGRAPHERS_URL}/{photographer.id}")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["id"] == photographer.id
        assert data["name"] == photographer.name
        assert "created_at" in data

    def test_not_found(self, api_client, db):
        resp = api_client.get(f"{PHOTOGRAPHERS_URL}/999999")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# Create (admin only)
# ---------------------------------------------------------------------------
class TestPhotographerCreate:
    PAYLOAD = {
        "id": 2001,
        "name": "New Photographer",
        "profile_url": "https://www.pexels.com/@newphoto",
    }

    def test_admin_can_create(self, admin_client):
        resp = admin_client.post(PHOTOGRAPHERS_URL, self.PAYLOAD, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert Photographer.objects.filter(id=2001).exists()
        assert Photographer.objects.get(id=2001).name == "New Photographer"

    def test_regular_user_forbidden(self, auth_client):
        resp = auth_client.post(PHOTOGRAPHERS_URL, self.PAYLOAD, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_anonymous_unauthorized(self, api_client, db):
        resp = api_client.post(PHOTOGRAPHERS_URL, self.PAYLOAD, format="json")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_name(self, admin_client):
        resp = admin_client.post(PHOTOGRAPHERS_URL, {"id": 2002}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Update (admin only)
# ---------------------------------------------------------------------------
class TestPhotographerUpdate:
    def test_admin_can_patch(self, admin_client, photographer):
        resp = admin_client.patch(
            f"{PHOTOGRAPHERS_URL}/{photographer.id}",
            {"name": "Updated Name"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        photographer.refresh_from_db()
        assert photographer.name == "Updated Name"

    def test_regular_user_forbidden(self, auth_client, photographer):
        resp = auth_client.patch(
            f"{PHOTOGRAPHERS_URL}/{photographer.id}",
            {"name": "Hacked"},
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_anonymous_unauthorized(self, api_client, photographer):
        resp = api_client.patch(
            f"{PHOTOGRAPHERS_URL}/{photographer.id}",
            {"name": "Hacked"},
            format="json",
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# Delete (admin only)
# ---------------------------------------------------------------------------
class TestPhotographerDelete:
    def test_admin_can_delete(self, admin_client, photographer):
        resp = admin_client.delete(f"{PHOTOGRAPHERS_URL}/{photographer.id}")
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not Photographer.objects.filter(id=photographer.id).exists()

    def test_regular_user_forbidden(self, auth_client, photographer):
        resp = auth_client.delete(f"{PHOTOGRAPHERS_URL}/{photographer.id}")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_anonymous_unauthorized(self, api_client, photographer):
        resp = api_client.delete(f"{PHOTOGRAPHERS_URL}/{photographer.id}")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_nonexistent(self, admin_client, db):
        resp = admin_client.delete(f"{PHOTOGRAPHERS_URL}/999999")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
