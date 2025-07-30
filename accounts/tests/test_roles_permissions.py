from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import Role, ModulePermission, Permissions, Roles
from accounts.utils import RoleManager, PermissionManager, UserPermissionManager

User = get_user_model()


class RolePermissionModelTest(TestCase):
    """Test the role and permission models."""

    def setUp(self):
        """Set up test data."""
        # Create permissions using get_or_create to avoid duplicates
        self.chat_view_perm, created = ModulePermission.objects.get_or_create(
            code=Permissions.CHAT_VIEW,
            defaults={
                'name': "Chat View",
                'description': "Can view chat conversations",
                'module': "chat"
            }
        )
        
        self.product_view_perm, created = ModulePermission.objects.get_or_create(
            code=Permissions.PRODUCT_VIEW,
            defaults={
                'name': "Product View",
                'description': "Can view products",
                'module': "product"
            }
        )
        
        self.product_edit_perm, created = ModulePermission.objects.get_or_create(
            code=Permissions.PRODUCT_UPDATE,
            defaults={
                'name': "Product Update",
                'description': "Can update products",
                'module': "product"
            }
        )
        
        # Create roles using get_or_create
        self.admin_role, created = Role.objects.get_or_create(
            name=Roles.ADMIN,
            defaults={
                'description': "Full system access",
                'is_system_role': True
            }
        )
        # Admin role already has all permissions from data migration, so we don't need to add them
        
        self.sales_agent_role, created = Role.objects.get_or_create(
            name=Roles.SALES_AGENT,
            defaults={
                'description': "Sales agent access",
                'is_system_role': True
            }
        )
        # Sales agent role already has the correct permissions from data migration
        
        # Create users
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="testpass123"
        )
        self.admin_user.roles.add(self.admin_role)
        
        self.sales_user = User.objects.create_user(
            email="sales@test.com",
            password="testpass123"
        )
        self.sales_user.roles.add(self.sales_agent_role)

    def test_permission_creation(self):
        """Test that permissions are created correctly."""
        self.assertEqual(self.chat_view_perm.code, Permissions.CHAT_VIEW)
        self.assertEqual(self.chat_view_perm.module, "chat")
        self.assertTrue(self.chat_view_perm.is_active)

    def test_role_creation(self):
        """Test that roles are created correctly."""
        self.assertEqual(self.admin_role.name, Roles.ADMIN)
        self.assertTrue(self.admin_role.is_system_role)
        # Admin role has all permissions from data migration, so count will be high
        self.assertGreater(self.admin_role.permissions.count(), 0)

    def test_user_permission_checking(self):
        """Test user permission checking methods."""
        # Admin should have all permissions
        self.assertTrue(self.admin_user.has_module_permission(Permissions.CHAT_VIEW))
        self.assertTrue(self.admin_user.has_module_permission(Permissions.PRODUCT_VIEW))
        self.assertTrue(self.admin_user.has_module_permission(Permissions.PRODUCT_UPDATE))
        
        # Sales agent should have limited permissions
        self.assertTrue(self.sales_user.has_module_permission(Permissions.CHAT_VIEW))
        self.assertTrue(self.sales_user.has_module_permission(Permissions.PRODUCT_VIEW))
        # Sales agent should not have product update permission
        self.assertFalse(self.sales_user.has_module_permission(Permissions.PRODUCT_UPDATE))

    def test_user_role_checking(self):
        """Test user role checking methods."""
        admin_roles = self.admin_user.get_user_roles()
        sales_roles = self.sales_user.get_user_roles()
        
        self.assertIn(Roles.ADMIN, admin_roles)
        self.assertIn(Roles.SALES_AGENT, sales_roles)

    def test_user_permission_methods(self):
        """Test user permission utility methods."""
        # Test has_any_permission
        self.assertTrue(self.admin_user.has_any_permission([
            Permissions.CHAT_VIEW, Permissions.PRODUCT_UPDATE
        ]))
        
        # Test has_all_permissions
        self.assertTrue(self.admin_user.has_all_permissions([
            Permissions.CHAT_VIEW, Permissions.PRODUCT_VIEW
        ]))
        
        # Sales user should not have all permissions
        self.assertFalse(self.sales_user.has_all_permissions([
            Permissions.CHAT_VIEW, Permissions.PRODUCT_UPDATE
        ]))


class RoleManagerTest(TestCase):
    """Test the RoleManager utility class."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@test.com",
            password="testpass123"
        )
        
        self.role = Role.objects.create(
            name="test_role",
            description="Test role"
        )

    def test_get_role_by_name(self):
        """Test getting a role by name."""
        role = RoleManager.get_role_by_name("test_role")
        self.assertEqual(role, self.role)
        
        # Test non-existent role
        role = RoleManager.get_role_by_name("non_existent")
        self.assertIsNone(role)

    def test_assign_role_to_user(self):
        """Test assigning a role to a user."""
        success = RoleManager.assign_role_to_user(self.user, "test_role")
        self.assertTrue(success)
        self.assertIn(self.role, self.user.roles.all())
        
        # Test assigning non-existent role
        success = RoleManager.assign_role_to_user(self.user, "non_existent")
        self.assertFalse(success)

    def test_remove_role_from_user(self):
        """Test removing a role from a user."""
        self.user.roles.add(self.role)
        success = RoleManager.remove_role_from_user(self.user, "test_role")
        self.assertTrue(success)
        self.assertNotIn(self.role, self.user.roles.all())

    def test_create_custom_role(self):
        """Test creating a custom role."""
        permissions = ["test.permission1", "test.permission2"]
        
        # Create permissions first using unique codes
        ModulePermission.objects.get_or_create(
            code="test.permission1", 
            defaults={'name': "Test Permission 1", 'module': "test"}
        )
        ModulePermission.objects.get_or_create(
            code="test.permission2", 
            defaults={'name': "Test Permission 2", 'module': "test"}
        )
        
        role = RoleManager.create_custom_role(
            name="custom_role",
            description="Custom role for testing",
            permissions=permissions
        )
        
        self.assertEqual(role.name, "custom_role")
        self.assertEqual(role.permissions.count(), 2)
        self.assertFalse(role.is_system_role)


class PermissionManagerTest(TestCase):
    """Test the PermissionManager utility class."""

    def setUp(self):
        """Set up test data."""
        self.permission, created = ModulePermission.objects.get_or_create(
            code="test.permission",
            defaults={
                'name': "Test Permission",
                'description': "Test permission",
                'module': "test"
            }
        )

    def test_get_permission_by_code(self):
        """Test getting a permission by code."""
        perm = PermissionManager.get_permission_by_code("test.permission")
        self.assertEqual(perm, self.permission)
        
        # Test non-existent permission
        perm = PermissionManager.get_permission_by_code("non.existent")
        self.assertIsNone(perm)

    def test_get_permissions_by_module(self):
        """Test getting permissions by module."""
        perms = PermissionManager.get_permissions_by_module("test")
        self.assertIn(self.permission, perms)

    def test_create_permission(self):
        """Test creating a new permission."""
        perm = PermissionManager.create_permission(
            code="new.permission",
            name="New Permission",
            description="New test permission",
            module="new"
        )
        
        self.assertEqual(perm.code, "new.permission")
        self.assertEqual(perm.module, "new")
        self.assertTrue(perm.is_active)


class UserPermissionManagerTest(TestCase):
    """Test the UserPermissionManager utility class."""

    def setUp(self):
        """Set up test data."""
        # Create permissions using get_or_create
        self.chat_view_perm, created = ModulePermission.objects.get_or_create(
            code=Permissions.CHAT_VIEW,
            defaults={
                'name': "Chat View",
                'module': "chat"
            }
        )
        
        self.product_view_perm, created = ModulePermission.objects.get_or_create(
            code=Permissions.PRODUCT_VIEW,
            defaults={
                'name': "Product View",
                'module': "product"
            }
        )
        
        # Create roles using get_or_create
        self.admin_role, created = Role.objects.get_or_create(
            name=Roles.ADMIN,
            defaults={'is_system_role': True}
        )
        # Admin role already has all permissions from data migration
        
        self.sales_role, created = Role.objects.get_or_create(
            name=Roles.SALES_AGENT,
            defaults={'is_system_role': True}
        )
        # Sales role already has the correct permissions from data migration
        
        # Create users
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="testpass123"
        )
        self.admin_user.roles.add(self.admin_role)
        
        self.sales_user = User.objects.create_user(
            email="sales@test.com",
            password="testpass123"
        )
        self.sales_user.roles.add(self.sales_role)

    def test_has_permission(self):
        """Test checking if user has a specific permission."""
        self.assertTrue(UserPermissionManager.has_permission(
            self.admin_user, Permissions.CHAT_VIEW
        ))
        self.assertTrue(UserPermissionManager.has_permission(
            self.sales_user, Permissions.CHAT_VIEW
        ))
        # Sales user should not have product view permission based on our setup
        # But since sales role has product.view from data migration, this will be True
        # Let's test with a permission that sales definitely doesn't have
        self.assertFalse(UserPermissionManager.has_permission(
            self.sales_user, Permissions.PRODUCT_UPDATE
        ))

    def test_has_any_permission(self):
        """Test checking if user has any of the specified permissions."""
        permissions = [Permissions.CHAT_VIEW, Permissions.PRODUCT_VIEW]
        
        self.assertTrue(UserPermissionManager.has_any_permission(
            self.admin_user, permissions
        ))
        self.assertTrue(UserPermissionManager.has_any_permission(
            self.sales_user, permissions
        ))

    def test_has_all_permissions(self):
        """Test checking if user has all of the specified permissions."""
        permissions = [Permissions.CHAT_VIEW, Permissions.PRODUCT_VIEW]
        
        self.assertTrue(UserPermissionManager.has_all_permissions(
            self.admin_user, permissions
        ))
        # Sales user should have both permissions from data migration
        self.assertTrue(UserPermissionManager.has_all_permissions(
            self.sales_user, permissions
        ))

    def test_role_checking_methods(self):
        """Test role checking utility methods."""
        self.assertTrue(UserPermissionManager.is_admin(self.admin_user))
        self.assertFalse(UserPermissionManager.is_admin(self.sales_user))
        
        self.assertTrue(UserPermissionManager.is_sales_agent(self.sales_user))
        self.assertFalse(UserPermissionManager.is_sales_agent(self.admin_user))

    def test_capability_checking_methods(self):
        """Test capability checking utility methods."""
        self.assertTrue(UserPermissionManager.can_access_chat(self.admin_user))
        self.assertTrue(UserPermissionManager.can_access_chat(self.sales_user))
        
        # Both admin and sales can view products based on data migration
        self.assertTrue(UserPermissionManager.can_view_products(self.admin_user))
        self.assertTrue(UserPermissionManager.can_view_products(self.sales_user))
        
        # But only admin should be able to edit products
        self.assertTrue(UserPermissionManager.can_edit_products(self.admin_user))
        self.assertFalse(UserPermissionManager.can_edit_products(self.sales_user))


class RolePermissionIntegrationTest(APITestCase):
    """Integration tests for role and permission system."""

    def setUp(self):
        """Set up test data."""
        # Create permissions using get_or_create
        self.chat_view_perm, created = ModulePermission.objects.get_or_create(
            code=Permissions.CHAT_VIEW,
            defaults={
                'name': "Chat View",
                'module': "chat"
            }
        )
        
        # Create roles using get_or_create
        self.admin_role, created = Role.objects.get_or_create(
            name=Roles.ADMIN,
            defaults={'is_system_role': True}
        )
        # Admin role already has all permissions from data migration
        
        # Create users
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="testpass123"
        )
        self.admin_user.roles.add(self.admin_role)
        
        self.regular_user = User.objects.create_user(
            email="user@test.com",
            password="testpass123"
        )

    def test_authentication_with_roles(self):
        """Test that users can authenticate and their roles are preserved."""
        # Login as admin user
        self.client.force_authenticate(user=self.admin_user)
        
        # Check that user has the expected permissions
        self.assertTrue(self.admin_user.has_module_permission(Permissions.CHAT_VIEW))
        self.assertIn(Roles.ADMIN, self.admin_user.get_user_roles())

    def test_permission_based_access(self):
        """Test that permissions control access to different parts of the system."""
        # Admin user should have chat access
        self.assertTrue(UserPermissionManager.can_access_chat(self.admin_user))
        
        # Regular user should not have chat access
        self.assertFalse(UserPermissionManager.can_access_chat(self.regular_user))


class PermissionConstantsTest(TestCase):
    """Test the permission constants."""

    def test_permission_constants_exist(self):
        """Test that all expected permission constants exist."""
        expected_permissions = [
            # Chat permissions
            Permissions.CHAT_VIEW,
            Permissions.CHAT_CREATE,
            Permissions.CHAT_UPDATE,
            Permissions.CHAT_DELETE,
            Permissions.CHAT_RESPOND,
            
            # Order permissions
            Permissions.ORDER_VIEW,
            Permissions.ORDER_CREATE,
            Permissions.ORDER_UPDATE,
            Permissions.ORDER_DELETE,
            Permissions.ORDER_PROCESS,
            
            # Product permissions
            Permissions.PRODUCT_VIEW,
            Permissions.PRODUCT_CREATE,
            Permissions.PRODUCT_UPDATE,
            Permissions.PRODUCT_DELETE,
            Permissions.PRODUCT_MANAGE_INVENTORY,
            
            # System permissions
            Permissions.SYSTEM_ADMIN,
            Permissions.SYSTEM_SETTINGS,
        ]
        
        for permission in expected_permissions:
            self.assertIsInstance(permission, str)
            self.assertNotEqual(permission, "")

    def test_role_constants_exist(self):
        """Test that all expected role constants exist."""
        expected_roles = [
            Roles.ADMIN,
            Roles.SALES_AGENT,
            Roles.INVENTORY_ADMIN,
        ]
        
        for role in expected_roles:
            self.assertIsInstance(role, str)
            self.assertNotEqual(role, "")

    def test_get_all_permissions_method(self):
        """Test the get_all_permissions class method."""
        permissions = Permissions.get_all_permissions()
        self.assertIsInstance(permissions, list)
        self.assertGreater(len(permissions), 0)
        
        # Check that all permissions are strings
        for permission in permissions:
            self.assertIsInstance(permission, str)

    def test_get_all_roles_method(self):
        """Test the get_all_roles class method."""
        roles = Roles.get_all_roles()
        self.assertIsInstance(roles, list)
        self.assertGreater(len(roles), 0)
        
        # Check that all roles are strings
        for role in roles:
            self.assertIsInstance(role, str) 