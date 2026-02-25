import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from photographers.models import Photographer
from photos.models import Photo

User = get_user_model()

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "strongpass123"

SAMPLE_SRC = {
    "original": "https://images.pexels.com/photos/1/photo.jpeg",
    "large2x": "https://images.pexels.com/photos/1/photo.jpeg?dpr=2&h=650&w=940",
    "large": "https://images.pexels.com/photos/1/photo.jpeg?h=650&w=940",
    "medium": "https://images.pexels.com/photos/1/photo.jpeg?h=350",
    "small": "https://images.pexels.com/photos/1/photo.jpeg?h=130",
    "portrait": "https://images.pexels.com/photos/1/photo.jpeg?fit=crop&h=1200&w=800",
    "landscape": "https://images.pexels.com/photos/1/photo.jpeg?fit=crop&h=627&w=1200",
    "tiny": "https://images.pexels.com/photos/1/photo.jpeg?fit=crop&h=200&w=280",
}


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(email=TEST_EMAIL, password=TEST_PASSWORD)


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin@example.com",
        password=TEST_PASSWORD,
        role=User.Role.ADMIN,
        is_staff=True,
    )


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def photographer(db):
    return Photographer.objects.create(
        id=1001,
        name="Jane Doe",
        profile_url="https://www.pexels.com/@janedoe",
    )


@pytest.fixture
def photographer_b(db):
    return Photographer.objects.create(
        id=1002,
        name="John Smith",
        profile_url="https://www.pexels.com/@johnsmith",
    )


@pytest.fixture
def photo(photographer):
    return Photo.objects.create(
        id=9001,
        photographer=photographer,
        width=3888,
        height=5184,
        url="https://www.pexels.com/photo/test-9001/",
        alt="A beautiful landscape",
        avg_color="#333831",
        src=SAMPLE_SRC,
    )


@pytest.fixture
def photo_b(photographer_b):
    return Photo.objects.create(
        id=9002,
        photographer=photographer_b,
        width=1920,
        height=1080,
        url="https://www.pexels.com/photo/test-9002/",
        alt="Urban cityscape",
        avg_color="#6D755E",
        src=SAMPLE_SRC,
    )
