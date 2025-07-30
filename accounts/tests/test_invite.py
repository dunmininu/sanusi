import django
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from unittest.mock import patch
from django.core import mail

django.setup()

User = get_user_model()


class InviteTests(TestCase):
    def setUp(self):
        from accounts.models import Role, ModulePermission

        perm = ModulePermission.objects.create(code="auth.manage_users", name="m")
        self.role = Role.objects.create(name="admin")
        self.role.permissions.add(perm)
        self.admin = User.objects.create_user(email="admin@example.com", password="pass")
        self.admin.roles.add(self.role)
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    @patch('accounts.views.settings.FRONTEND_BASE_URL', 'http://localhost:3000')
    def test_invite_and_accept_flow(self):
        from accounts.models import Invite

        # Test invitation creation
        res = self.client.post(
            "/api/auth/invite/",
            {"email": "new@example.com", "roles": [str(self.role.id)]},
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        
        # Verify invite was created
        invite = Invite.objects.get(email="new@example.com")
        self.assertIsNotNone(invite.token)
        self.assertEqual(invite.email, "new@example.com")
        self.assertEqual(invite.invited_by, self.admin)
        self.assertFalse(invite.is_used)
        
        # Test accepting invitation with new required fields
        self.client.logout()
        res = self.client.post(
            "/api/auth/accept-invite/",
            {
                "token": invite.token, 
                "password": "secret123",
                "first_name": "John",
                "last_name": "Doe"
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        
        # Verify user was created with correct fields
        user = User.objects.get(email="new@example.com")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")
        self.assertTrue(user.check_password("secret123"))
        self.assertTrue(user.is_active)
        
        # Verify invite was marked as used
        invite.refresh_from_db()
        self.assertTrue(invite.is_used)
        
        # Verify response contains expected fields
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)
        self.assertIn("user", res.data)
        self.assertEqual(res.data["user"]["email"], "new@example.com")
        self.assertEqual(res.data["user"]["first_name"], "John")
        self.assertEqual(res.data["user"]["last_name"], "Doe")

    def test_invite_with_custom_message(self):
        from accounts.models import Invite

        # Test invitation with custom message
        res = self.client.post(
            "/api/auth/invite/",
            {
                "email": "test@example.com", 
                "roles": [str(self.role.id)],
                "message": "Welcome to our team!"
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        
        # Verify invite was created with message
        invite = Invite.objects.get(email="test@example.com")
        self.assertIsNotNone(invite.token)

    def test_accept_invite_missing_required_fields(self):
        from accounts.models import Invite

        # Create an invite first
        from django.utils import timezone
        invite = Invite.objects.create(
            email="test@example.com",
            token="test-token",
            invited_by=self.admin,
            expires_at=timezone.now() + timezone.timedelta(days=7)
        )

        # Test missing first_name
        res = self.client.post(
            "/api/auth/accept-invite/",
            {
                "token": invite.token,
                "password": "secret123",
                "last_name": "Doe"
            },
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("first_name", res.data)

        # Test missing last_name
        res = self.client.post(
            "/api/auth/accept-invite/",
            {
                "token": invite.token,
                "password": "secret123",
                "first_name": "John"
            },
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("last_name", res.data)

    def test_accept_invite_invalid_token(self):
        res = self.client.post(
            "/api/auth/accept-invite/",
            {
                "token": "invalid-token",
                "password": "secret123",
                "first_name": "John",
                "last_name": "Doe"
            },
            format="json",
        )
        self.assertEqual(res.status_code, 404)

    def test_accept_invite_expired_token(self):
        from accounts.models import Invite
        from django.utils import timezone

        # Create expired invite
        invite = Invite.objects.create(
            email="expired@example.com",
            token="expired-token",
            invited_by=self.admin,
            expires_at=timezone.now() - timezone.timedelta(days=1)
        )

        res = self.client.post(
            "/api/auth/accept-invite/",
            {
                "token": invite.token,
                "password": "secret123",
                "first_name": "John",
                "last_name": "Doe"
            },
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("error", res.data)

    def test_accept_invite_user_already_exists(self):
        from accounts.models import Invite

        # Create existing user
        User.objects.create_user(email="existing@example.com", password="pass")

        # Create invite for existing user
        from django.utils import timezone
        invite = Invite.objects.create(
            email="existing@example.com",
            token="existing-token",
            invited_by=self.admin,
            expires_at=timezone.now() + timezone.timedelta(days=7)
        )

        res = self.client.post(
            "/api/auth/accept-invite/",
            {
                "token": invite.token,
                "password": "secret123",
                "first_name": "John",
                "last_name": "Doe"
            },
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("error", res.data)

    def test_has_scopes_permission(self):
        from sanusi_backend.permissions import HasScopes

        user = User.objects.create_user(email="u@example.com", password="p")
        user.roles.add(self.role)
        request = type("req", (), {"user": user})()
        perm_obj = HasScopes()
        view = type("view", (), {"required_scopes": ["auth.manage_users"]})()
        self.assertTrue(perm_obj.has_permission(request, view))
