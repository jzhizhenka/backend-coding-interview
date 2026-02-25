import jwt
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
REFRESH_URL = "/api/auth/refresh"
ME_URL = "/api/users/me"

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "strongpass123"


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------
class TestUserModel:
    def test_create_user(self, db):
        user = User.objects.create_user(email=TEST_EMAIL, password=TEST_PASSWORD)
        assert user.email == TEST_EMAIL
        assert user.check_password(TEST_PASSWORD)
        assert user.role == User.Role.USER
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_create_user_normalizes_email(self, db):
        user = User.objects.create_user(email="Test@EXAMPLE.com", password=TEST_PASSWORD)
        assert user.email == "Test@example.com"

    def test_create_user_without_email_raises(self, db):
        with pytest.raises(ValueError, match="Email is required"):
            User.objects.create_user(email="", password=TEST_PASSWORD)

    def test_create_superuser(self, db):
        admin = User.objects.create_superuser(email="admin@example.com", password=TEST_PASSWORD)
        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.role == User.Role.ADMIN

    def test_str_returns_email(self, user):
        assert str(user) == TEST_EMAIL


# ---------------------------------------------------------------------------
# Registration tests
# ---------------------------------------------------------------------------
class TestRegister:
    def test_success(self, api_client, db):
        resp = api_client.post(REGISTER_URL, {"email": TEST_EMAIL, "password": TEST_PASSWORD})
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["user"]["email"] == TEST_EMAIL
        assert "id" in data["user"]
        assert "password" not in data["user"]
        assert User.objects.filter(email=TEST_EMAIL).exists()

    def test_duplicate_email(self, api_client, user):
        resp = api_client.post(REGISTER_URL, {"email": TEST_EMAIL, "password": TEST_PASSWORD})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_duplicate_email_case_insensitive(self, api_client, user):
        resp = api_client.post(REGISTER_URL, {"email": "TEST@EXAMPLE.COM", "password": TEST_PASSWORD})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_short_password(self, api_client, db):
        resp = api_client.post(REGISTER_URL, {"email": TEST_EMAIL, "password": "short"})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_email(self, api_client, db):
        resp = api_client.post(REGISTER_URL, {"password": TEST_PASSWORD})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_password(self, api_client, db):
        resp = api_client.post(REGISTER_URL, {"email": TEST_EMAIL})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_email_format(self, api_client, db):
        resp = api_client.post(REGISTER_URL, {"email": "not-an-email", "password": TEST_PASSWORD})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Login tests
# ---------------------------------------------------------------------------
class TestLogin:
    def test_success(self, api_client, user):
        resp = api_client.post(LOGIN_URL, {"email": TEST_EMAIL, "password": TEST_PASSWORD})
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"
        assert data["expires_in"] == 900

    def test_case_insensitive_email(self, api_client, user):
        resp = api_client.post(LOGIN_URL, {"email": "TEST@EXAMPLE.COM", "password": TEST_PASSWORD})
        assert resp.status_code == status.HTTP_200_OK

    def test_wrong_password(self, api_client, user):
        resp = api_client.post(LOGIN_URL, {"email": TEST_EMAIL, "password": "wrongpass123"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid" in resp.json()["detail"]

    def test_nonexistent_user(self, api_client, db):
        resp = api_client.post(LOGIN_URL, {"email": "nobody@example.com", "password": TEST_PASSWORD})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_fields(self, api_client, db):
        resp = api_client.post(LOGIN_URL, {})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Token claims tests
# ---------------------------------------------------------------------------
class TestTokenClaims:
    @staticmethod
    def _decode_token(token):
        return jwt.decode(token, options={"verify_signature": False}, algorithms=["HS256"])

    def test_access_token_contains_custom_claims(self, api_client, user):
        resp = api_client.post(LOGIN_URL, {"email": TEST_EMAIL, "password": TEST_PASSWORD})
        token = resp.json()["access_token"]
        payload = self._decode_token(token)
        assert payload["sub"] == str(user.id)
        assert payload["email"] == user.email
        assert payload["role"] == "user"
        assert "exp" in payload
        assert "iat" in payload

    def test_admin_token_has_admin_role(self, api_client, admin_user):
        resp = api_client.post(
            LOGIN_URL,
            {"email": "admin@example.com", "password": TEST_PASSWORD},
        )
        token = resp.json()["access_token"]
        payload = self._decode_token(token)
        assert payload["role"] == "admin"


# ---------------------------------------------------------------------------
# Refresh tests
# ---------------------------------------------------------------------------
class TestRefresh:
    def test_success(self, api_client, user):
        login_resp = api_client.post(LOGIN_URL, {"email": TEST_EMAIL, "password": TEST_PASSWORD})
        refresh_token = login_resp.json()["refresh_token"]

        resp = api_client.post(REFRESH_URL, {"refresh_token": refresh_token})
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "access_token" in data
        assert data["expires_in"] == 900

    def test_invalid_token(self, api_client, db):
        resp = api_client.post(REFRESH_URL, {"refresh_token": "invalid.token.value"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_token(self, api_client, db):
        resp = api_client.post(REFRESH_URL, {})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Me endpoint tests
# ---------------------------------------------------------------------------
class TestMe:
    def test_authenticated(self, auth_client, user):
        resp = auth_client.get(ME_URL)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["id"] == user.id
        assert data["email"] == user.email
        assert data["role"] == "user"
        assert "created_at" in data
        assert "updated_at" in data

    def test_unauthenticated(self, api_client, db):
        resp = api_client.get(ME_URL)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_current_user_only(self, db):
        user_a = User.objects.create_user(email="a@example.com", password=TEST_PASSWORD)
        User.objects.create_user(email="b@example.com", password=TEST_PASSWORD)

        client = APIClient()
        client.force_authenticate(user=user_a)
        resp = client.get(ME_URL)
        assert resp.json()["email"] == "a@example.com"
