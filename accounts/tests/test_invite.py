import django
from django.conf import settings
from django.contrib.auth import get_user_model  # noqa: E402
from django.test import TestCase  # noqa: E402
from rest_framework.test import APIClient  # noqa: E402

django.setup()
settings.DATABASES["default"] = {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": ":memory:",
}
from django.db import connections  # noqa: E402
connections.databases["default"] = settings.DATABASES["default"]

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

    def test_invite_and_accept_flow(self):
        from accounts.models import Invite

        res = self.client.post(
            "/api/auth/invite/",
            {"email": "new@example.com", "roles": [str(self.role.id)]},
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        token = Invite.objects.get(email="new@example.com").token

        self.client.logout()
        res = self.client.post(
            "/api/auth/accept-invite/",
            {"token": token, "password": "secret"},
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        self.assertTrue(User.objects.filter(email="new@example.com").exists())

    def test_has_scopes_permission(self):
        from sanusi_backend.permissions import HasScopes

        user = User.objects.create_user(email="u@example.com", password="p")
        user.roles.add(self.role)
        request = type("req", (), {"user": user})()
        perm_obj = HasScopes()
        view = type("view", (), {"required_scopes": ["auth.manage_users"]})()
        self.assertTrue(perm_obj.has_permission(request, view))
