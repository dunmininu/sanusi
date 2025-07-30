"""
Basic tests that don't rely on complex migrations.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class BasicModelTests(TestCase):
    """Test basic model functionality without complex migrations."""
    
    def test_user_creation(self):
        """Test that users can be created"""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )
        
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.first_name, "Test")
        self.assertEqual(user.last_name, "User")
        self.assertTrue(user.check_password("testpass123"))
        self.assertTrue(user.is_active)
        
    def test_user_manager(self):
        """Test the custom user manager"""
        user = User.objects.create_user(
            email="manager@example.com",
            password="managerpass123"
        )
        
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        
        # Test superuser creation
        superuser = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123"
        )
        
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
        
    def test_user_string_representation(self):
        """Test user string representation"""
        user = User.objects.create_user(
            email="string@example.com",
            password="stringpass123",
            first_name="String",
            last_name="User"
        )
        
        # The string representation should include the name
        self.assertIn("String", str(user))
        self.assertIn("User", str(user))


class BasicAPITests(TestCase):
    """Test basic API functionality."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="apitest@example.com",
            password="apitest123",
            first_name="API",
            last_name="Test"
        )
        
    def test_user_profile_endpoint(self):
        """Test the user profile endpoint"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get("/api/auth/profile/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "apitest@example.com")
        self.assertEqual(response.data["first_name"], "API")
        self.assertEqual(response.data["last_name"], "Test")
        
    def test_unauthenticated_profile_access(self):
        """Test that unauthenticated users can't access profile"""
        response = self.client.get("/api/auth/profile/")
        self.assertEqual(response.status_code, 401)
        
    def test_user_login(self):
        """Test user login functionality"""
        response = self.client.post(
            "/api/auth/login/",
            {
                "email": "apitest@example.com",
                "password": "apitest123"
            },
            format="json"
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)
        
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        response = self.client.post(
            "/api/auth/login/",
            {
                "email": "apitest@example.com",
                "password": "wrongpassword"
            },
            format="json"
        )
        
        self.assertEqual(response.status_code, 401)
        
    def test_user_registration(self):
        """Test user registration"""
        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "newuser@example.com",
                "password": "newuser123",
                "password_confirm": "newuser123",
                "first_name": "New",
                "last_name": "User"
            },
            format="json"
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertIn("email", response.data)
        self.assertEqual(response.data["email"], "newuser@example.com")
        
        # Verify user was created
        user = User.objects.get(email="newuser@example.com")
        self.assertEqual(user.first_name, "New")
        self.assertEqual(user.last_name, "User")
        
    def test_registration_password_mismatch(self):
        """Test registration with mismatched passwords"""
        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "mismatch@example.com",
                "password": "password123",
                "password_confirm": "different123",
                "first_name": "Mismatch",
                "last_name": "User"
            },
            format="json"
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("password_confirm", response.data)
        
    def test_registration_duplicate_email(self):
        """Test registration with duplicate email"""
        # Create first user
        User.objects.create_user(
            email="duplicate@example.com",
            password="pass123"
        )
        
        # Try to register with same email
        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "duplicate@example.com",
                "password": "pass123",
                "password_confirm": "pass123",
                "first_name": "Duplicate",
                "last_name": "User"
            },
            format="json"
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data) 