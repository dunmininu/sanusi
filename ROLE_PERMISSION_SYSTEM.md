# Role and Permission System Documentation

## Overview

The Sanusi platform implements a comprehensive role-based access control (RBAC) system that provides granular permissions for different user types. This system is designed to be flexible, scalable, and easy to extend.

## Core Components

### 1. Permissions

Permissions are the fundamental building blocks of the access control system. Each permission represents a specific action or capability within the system.

#### Permission Structure
- **Code**: Unique identifier (e.g., `chat.view`, `product.update`)
- **Name**: Human-readable name (e.g., "Chat View", "Product Update")
- **Description**: Detailed description of what the permission allows
- **Module**: The module this permission belongs to (e.g., "chat", "product")
- **Active Status**: Whether the permission is currently active

#### Available Permission Categories

##### Chat Permissions
- `chat.view` - Can view chat conversations
- `chat.create` - Can create new chat conversations
- `chat.update` - Can update chat conversations
- `chat.delete` - Can delete chat conversations
- `chat.respond` - Can respond to chat messages

##### Order Permissions
- `order.view` - Can view orders
- `order.create` - Can create new orders
- `order.update` - Can update orders
- `order.delete` - Can delete orders
- `order.process` - Can process orders

##### Product Permissions
- `product.view` - Can view products
- `product.create` - Can create new products
- `product.update` - Can update products
- `product.delete` - Can delete products
- `product.manage_inventory` - Can manage product inventory

##### Customer Permissions
- `customer.view` - Can view customers
- `customer.create` - Can create new customers
- `customer.update` - Can update customers
- `customer.delete` - Can delete customers

##### Business Permissions
- `business.view` - Can view business information
- `business.create` - Can create new businesses
- `business.update` - Can update business information
- `business.delete` - Can delete businesses

##### User Management Permissions
- `user.view` - Can view users
- `user.create` - Can create new users
- `user.update` - Can update users
- `user.delete` - Can delete users
- `user.invite` - Can invite new users

##### Analytics Permissions
- `analytics.view` - Can view analytics
- `analytics.export` - Can export analytics data

##### System Permissions
- `system.admin` - Full system administration access
- `system.settings` - Can manage system settings

### 2. Roles

Roles are collections of permissions that define what a user can do within the system. Each user can have multiple roles.

#### System Roles

##### Admin Role
- **Description**: Full system access with all permissions
- **Permissions**: All permissions in the system
- **Use Case**: System administrators who need complete access

##### Sales Agent Role
- **Description**: Access to chat interface, orders, and view-only product access
- **Permissions**:
  - Chat: view, create, update, respond
  - Orders: view, create, update, process
  - Products: view only
  - Customers: view, create, update
  - Business: view
- **Use Case**: Customer service representatives who handle customer interactions

##### Inventory Admin Role
- **Description**: Access to product management and all sales agent permissions
- **Permissions**: All Sales Agent permissions plus:
  - Products: create, update, delete, manage inventory
- **Use Case**: Inventory managers who need to manage products and handle customer interactions

#### Custom Roles

The system supports creating custom roles with specific permission combinations to meet unique business requirements.

### 3. User Management

Users can be assigned multiple roles, and their effective permissions are the union of all their role permissions.

## Implementation Details

### Database Models

#### ModulePermission
```python
class ModulePermission(BaseModel):
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    module = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
```

#### Role
```python
class Role(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    permissions = models.ManyToManyField(ModulePermission, related_name="roles", blank=True)
    is_owner = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    is_system_role = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
```

#### User (Extended)
```python
# Users have a many-to-many relationship with roles
roles = models.ManyToManyField(Role, related_name="users", blank=True)
```

### Permission Classes

The system provides several permission classes for use in Django REST Framework views:

#### Basic Permission Classes
- `HasScopes`: Requires all specified permissions
- `HasAnyScope`: Requires any of the specified permissions
- `HasAllScopes`: Requires all of the specified permissions

#### Module-Specific Permission Classes
- `ChatPermissions.CanViewChat`
- `ChatPermissions.CanCreateChat`
- `ChatPermissions.CanUpdateChat`
- `ChatPermissions.CanDeleteChat`
- `ChatPermissions.CanRespondToChat`
- `OrderPermissions.CanViewOrder`
- `OrderPermissions.CanCreateOrder`
- `OrderPermissions.CanUpdateOrder`
- `OrderPermissions.CanDeleteOrder`
- `OrderPermissions.CanProcessOrder`
- `ProductPermissions.CanViewProduct`
- `ProductPermissions.CanCreateProduct`
- `ProductPermissions.CanUpdateProduct`
- `ProductPermissions.CanDeleteProduct`
- `ProductPermissions.CanManageInventory`
- `CustomerPermissions.CanViewCustomer`
- `CustomerPermissions.CanCreateCustomer`
- `CustomerPermissions.CanUpdateCustomer`
- `CustomerPermissions.CanDeleteCustomer`
- `BusinessPermissions.CanViewBusiness`
- `BusinessPermissions.CanCreateBusiness`
- `BusinessPermissions.CanUpdateBusiness`
- `BusinessPermissions.CanDeleteBusiness`
- `UserPermissions.CanViewUser`
- `UserPermissions.CanCreateUser`
- `UserPermissions.CanUpdateUser`
- `UserPermissions.CanDeleteUser`
- `UserPermissions.CanInviteUser`
- `AnalyticsPermissions.CanViewAnalytics`
- `AnalyticsPermissions.CanExportAnalytics`
- `SystemPermissions.IsSystemAdmin`
- `SystemPermissions.CanManageSettings`

#### Convenience Permission Classes
- `SalesAgentPermissions`: Checks for sales agent capabilities
- `InventoryAdminPermissions`: Checks for inventory admin capabilities
- `AdminPermissions`: Checks for admin capabilities

### Utility Classes

#### RoleManager
Provides utility methods for role management:
- `get_role_by_name(role_name)`
- `get_all_roles()`
- `get_system_roles()`
- `create_custom_role(name, description, permissions)`
- `assign_role_to_user(user, role_name)`
- `remove_role_from_user(user, role_name)`
- `get_user_roles(user)`
- `get_user_role_names(user)`

#### PermissionManager
Provides utility methods for permission management:
- `get_permission_by_code(code)`
- `get_permissions_by_module(module)`
- `get_all_permissions()`
- `create_permission(code, name, description, module)`

#### UserPermissionManager
Provides utility methods for checking user permissions:
- `has_permission(user, permission_code)`
- `has_any_permission(user, permission_codes)`
- `has_all_permissions(user, permission_codes)`
- `get_user_permissions(user)`
- `is_admin(user)`
- `is_sales_agent(user)`
- `is_inventory_admin(user)`
- `can_access_chat(user)`
- `can_respond_to_chat(user)`
- `can_view_orders(user)`
- `can_process_orders(user)`
- `can_view_products(user)`
- `can_edit_products(user)`
- `can_manage_inventory(user)`

## Usage Examples

### 1. Setting Up Roles and Permissions

```bash
# Run the setup command
python manage.py setup_roles --create-admin

# Assign admin role to existing user
python manage.py setup_roles --user-email admin@example.com
```

### 2. Using Permission Classes in Views

```python
from rest_framework.permissions import IsAuthenticated
from sanusi_backend.permissions import (
    HasScopes, ChatPermissions, OrderPermissions, ProductPermissions
)

class ChatViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, ChatPermissions.CanViewChat]
    
    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated, ChatPermissions.CanCreateChat]
        elif self.action in ['update', 'partial_update']:
            return [IsAuthenticated, ChatPermissions.CanUpdateChat]
        elif self.action == 'destroy':
            return [IsAuthenticated, ChatPermissions.CanDeleteChat]
        return [IsAuthenticated, ChatPermissions.CanViewChat]

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, OrderPermissions.CanViewOrder]
    required_scopes = ['order.view']

class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, ProductPermissions.CanViewProduct]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated, ProductPermissions.CanUpdateProduct]
        return [IsAuthenticated, ProductPermissions.CanViewProduct]
```

### 3. Checking Permissions in Code

```python
from accounts.utils import UserPermissionManager, RoleManager

# Check if user can perform specific actions
if UserPermissionManager.can_access_chat(user):
    # Allow chat access
    pass

if UserPermissionManager.can_edit_products(user):
    # Allow product editing
    pass

# Assign roles to users
RoleManager.assign_role_to_user(user, 'sales_agent')

# Create custom role
custom_role = RoleManager.create_custom_role(
    name='support_agent',
    description='Customer support with limited access',
    permissions=['chat.view', 'chat.respond', 'customer.view']
)
```

### 4. Adding New Permissions

To add new permissions to the system:

1. Add the permission constant to `accounts.models.Permissions`
2. Create the permission in the database
3. Update relevant roles to include the new permission
4. Create appropriate permission classes if needed

```python
# In accounts/models.py
class Permissions:
    # ... existing permissions ...
    NEW_FEATURE_VIEW = "new_feature.view"
    NEW_FEATURE_EDIT = "new_feature.edit"

# Create permission classes
class NewFeaturePermissions:
    class CanViewNewFeature(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.NEW_FEATURE_VIEW)
    
    class CanEditNewFeature(BasePermission):
        def has_permission(self, request, view):
            return request.user.has_module_permission(Permissions.NEW_FEATURE_EDIT)
```

### 5. Creating Custom Roles

```python
from accounts.utils import RoleManager

# Create a custom role for a specific business need
support_role = RoleManager.create_custom_role(
    name='tier2_support',
    description='Tier 2 support with extended permissions',
    permissions=[
        'chat.view', 'chat.respond', 'chat.update',
        'order.view', 'order.update',
        'customer.view', 'customer.update',
        'product.view'
    ]
)

# Assign the role to a user
RoleManager.assign_role_to_user(user, 'tier2_support')
```

## Migration and Setup

### Running Migrations

```bash
# Apply the schema migrations
python manage.py migrate accounts

# Run the data migration to create initial roles and permissions
python manage.py migrate accounts 0011_initial_roles_and_permissions_data
```

### Management Commands

The system includes a management command for setting up roles and permissions:

```bash
# Set up roles and permissions
python manage.py setup_roles

# Create a default admin user
python manage.py setup_roles --create-admin

# Assign admin role to existing user
python manage.py setup_roles --user-email admin@example.com
```

## Best Practices

### 1. Permission Design
- Use descriptive permission codes (e.g., `chat.respond` instead of `chat.msg`)
- Group related permissions by module
- Keep permissions granular for maximum flexibility

### 2. Role Design
- Start with the three system roles (Admin, Sales Agent, Inventory Admin)
- Create custom roles only when necessary
- Document the purpose and permissions of each custom role

### 3. Security Considerations
- Always check permissions in views, not just in templates
- Use the most restrictive permission class that meets your needs
- Regularly audit user roles and permissions
- Consider implementing permission caching for performance

### 4. Performance Optimization
- Use `select_related` and `prefetch_related` when querying users with roles
- Consider caching user permissions for frequently accessed data
- Use database indexes on permission and role lookups

## Extending the System

The role and permission system is designed to be easily extensible:

1. **Adding New Modules**: Create new permission constants and classes
2. **Adding New Roles**: Use the RoleManager to create custom roles
3. **Adding New Permission Types**: Extend the permission classes as needed
4. **Integrating with External Systems**: Use the utility classes to integrate with external authentication systems

## Troubleshooting

### Common Issues

1. **Permission Not Working**: Ensure the permission is active and assigned to the user's role
2. **Role Not Assigned**: Check that the role exists and is active
3. **Migration Errors**: Ensure all migrations are applied in order
4. **Performance Issues**: Consider adding database indexes or caching

### Debugging

```python
# Check user permissions
user_permissions = user.get_user_permissions()
print(f"User permissions: {user_permissions}")

# Check user roles
user_roles = user.get_user_roles()
print(f"User roles: {user_roles}")

# Check specific permission
has_permission = user.has_module_permission('chat.view')
print(f"Can view chat: {has_permission}")
```

This role and permission system provides a solid foundation for access control in the Sanusi platform while maintaining flexibility for future growth and customization.

## Role Permissions Matrix

| Permission | Admin | Sales Agent | Inventory Admin |
|------------|-------|-------------|-----------------|
| **Chat Permissions** |
| `chat.view` | yes | yes | yes |
| `chat.create` | yes | yes | yes |
| `chat.update` | yes | yes | yes |
| `chat.delete` | yes | no | no |
| `chat.respond` | yes | yes | yes |
| **Order Permissions** |
| `order.view` | yes | yes | yes |
| `order.create` | yes | yes | yes |
| `order.update` | yes | yes | yes |
| `order.delete` | yes | no | no |
| `order.process` | yes | yes | yes |
| **Product Permissions** |
| `product.view` | yes | yes | yes |
| `product.create` | yes | no | yes |
| `product.update` | yes | no | yes |
| `product.delete` | yes | no | yes |
| `product.manage_inventory` | yes | no | yes |
| **Customer Permissions** |
| `customer.view` | yes | yes | yes |
| `customer.create` | yes | yes | yes |
| `customer.update` | yes | yes | yes |
| `customer.delete` | yes | no | no |
| **Business Permissions** |
| `business.view` | yes | yes | yes |
| `business.create` | yes | no | no |
| `business.update` | yes | no | no |
| `business.delete` | yes | no | no |
| **User Management Permissions** |
| `user.view` | yes | no | no |
| `user.create` | yes | no | no |
| `user.update` | yes | no | no |
| `user.delete` | yes | no | no |
| `user.invite` | yes | no | no |
| **Analytics Permissions** |
| `analytics.view` | yes | no | no |
| `analytics.export` | yes | no | no |
| **System Permissions** |
| `system.admin` | yes | no | no |
| `system.settings` | yes | no | no |



Role Permissions Matrix Features
Complete Permission Coverage
- 32 permissions across 8 modules
- 3 roles (Admin, Sales Agent, Inventory Admin)
- Clear visual indicators (yes for granted, no for denied)

Organized by Module
- Chat Permissions (5 permissions)
- Order Permissions (5 permissions)
- Product Permissions (5 permissions)
- Customer Permissions (4 permissions)
- Business Permissions (4 permissions)
- User Management Permissions (5 permissions)
- Analytics Permissions (2 permissions)
- System Permissions (2 permissions)

Key Insights from the Matrix
- Admin Role: Full access to all 32 permissions
- Sales Agent Role: Focused on customer-facing operations
    - Chat: Can view, create, update, respond (no delete)
    - Orders: Can view, create, update, process (no delete)
    - Products: View only
    - Customers: Can view, create, update (no delete)
    - Business: View only
- Inventory Admin Role: Sales Agent + Product Management
    - All Sales Agent permissions
    - Plus full product management capabilities
    
The matrix provides a clear, at-a-glance view of what each role can and cannot do, making it easy for developers and administrators to understand the permission structure and for business stakeholders to review access levels.