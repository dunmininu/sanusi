from django.db import migrations
from accounts.models import Permissions, Roles


def create_initial_permissions(apps, schema_editor):
    """Create initial permissions for the system."""
    ModulePermission = apps.get_model('accounts', 'ModulePermission')
    
    # Define all permissions with their modules
    permissions_data = [
        # Chat permissions
        ('chat.view', 'Chat View', 'Can view chat conversations', 'chat'),
        ('chat.create', 'Chat Create', 'Can create new chat conversations', 'chat'),
        ('chat.update', 'Chat Update', 'Can update chat conversations', 'chat'),
        ('chat.delete', 'Chat Delete', 'Can delete chat conversations', 'chat'),
        ('chat.respond', 'Chat Respond', 'Can respond to chat messages', 'chat'),
        
        # Order permissions
        ('order.view', 'Order View', 'Can view orders', 'order'),
        ('order.create', 'Order Create', 'Can create new orders', 'order'),
        ('order.update', 'Order Update', 'Can update orders', 'order'),
        ('order.delete', 'Order Delete', 'Can delete orders', 'order'),
        ('order.process', 'Order Process', 'Can process orders', 'order'),
        
        # Product permissions
        ('product.view', 'Product View', 'Can view products', 'product'),
        ('product.create', 'Product Create', 'Can create new products', 'product'),
        ('product.update', 'Product Update', 'Can update products', 'product'),
        ('product.delete', 'Product Delete', 'Can delete products', 'product'),
        ('product.manage_inventory', 'Product Manage Inventory', 'Can manage product inventory', 'product'),
        
        # Customer permissions
        ('customer.view', 'Customer View', 'Can view customers', 'customer'),
        ('customer.create', 'Customer Create', 'Can create new customers', 'customer'),
        ('customer.update', 'Customer Update', 'Can update customers', 'customer'),
        ('customer.delete', 'Customer Delete', 'Can delete customers', 'customer'),
        
        # Business permissions
        ('business.view', 'Business View', 'Can view business information', 'business'),
        ('business.create', 'Business Create', 'Can create new businesses', 'business'),
        ('business.update', 'Business Update', 'Can update business information', 'business'),
        ('business.delete', 'Business Delete', 'Can delete businesses', 'business'),
        
        # User management permissions
        ('user.view', 'User View', 'Can view users', 'user'),
        ('user.create', 'User Create', 'Can create new users', 'user'),
        ('user.update', 'User Update', 'Can update users', 'user'),
        ('user.delete', 'User Delete', 'Can delete users', 'user'),
        ('user.invite', 'User Invite', 'Can invite new users', 'user'),
        
        # Analytics permissions
        ('analytics.view', 'Analytics View', 'Can view analytics', 'analytics'),
        ('analytics.export', 'Analytics Export', 'Can export analytics data', 'analytics'),
        
        # System permissions
        ('system.admin', 'System Admin', 'Full system administration access', 'system'),
        ('system.settings', 'System Settings', 'Can manage system settings', 'system'),
    ]
    
    for code, name, description, module in permissions_data:
        ModulePermission.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'description': description,
                'module': module,
                'is_active': True,
            }
        )


def create_initial_roles(apps, schema_editor):
    """Create initial roles with their permissions."""
    Role = apps.get_model('accounts', 'Role')
    ModulePermission = apps.get_model('accounts', 'ModulePermission')
    
    # Create Admin role - full access
    admin_role, created = Role.objects.get_or_create(
        name=Roles.ADMIN,
        defaults={
            'description': 'Full system access with all permissions',
            'is_system_role': True,
            'is_active': True,
        }
    )
    
    # Admin gets all permissions
    all_permissions = ModulePermission.objects.filter(is_active=True)
    admin_role.permissions.set(all_permissions)
    
    # Create Sales Agent role
    sales_agent_role, created = Role.objects.get_or_create(
        name=Roles.SALES_AGENT,
        defaults={
            'description': 'Access to chat interface, orders, and view-only product access',
            'is_system_role': True,
            'is_active': True,
        }
    )
    
    # Sales Agent permissions
    sales_agent_permissions = [
        'chat.view', 'chat.create', 'chat.update', 'chat.respond',
        'order.view', 'order.create', 'order.update', 'order.process',
        'product.view',  # View only access
        'customer.view', 'customer.create', 'customer.update',
        'business.view',
    ]
    
    sales_agent_perms = ModulePermission.objects.filter(
        code__in=sales_agent_permissions,
        is_active=True
    )
    sales_agent_role.permissions.set(sales_agent_perms)
    
    # Create Inventory Admin role
    inventory_admin_role, created = Role.objects.get_or_create(
        name=Roles.INVENTORY_ADMIN,
        defaults={
            'description': 'Access to product management and all sales agent permissions',
            'is_system_role': True,
            'is_active': True,
        }
    )
    
    # Inventory Admin permissions (Sales Agent + Product management)
    inventory_admin_permissions = sales_agent_permissions + [
        'product.create', 'product.update', 'product.delete', 'product.manage_inventory',
    ]
    
    inventory_admin_perms = ModulePermission.objects.filter(
        code__in=inventory_admin_permissions,
        is_active=True
    )
    inventory_admin_role.permissions.set(inventory_admin_perms)


def reverse_create_initial_roles_and_permissions(apps, schema_editor):
    """Reverse the creation of initial roles and permissions."""
    Role = apps.get_model('accounts', 'Role')
    ModulePermission = apps.get_model('accounts', 'ModulePermission')
    
    # Delete roles
    Role.objects.filter(
        name__in=[Roles.ADMIN, Roles.SALES_AGENT, Roles.INVENTORY_ADMIN]
    ).delete()
    
    # Delete permissions
    ModulePermission.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0010_add_initial_roles_and_permissions'),
    ]

    operations = [
        migrations.RunPython(
            create_initial_permissions,
            reverse_create_initial_roles_and_permissions
        ),
        migrations.RunPython(
            create_initial_roles,
            reverse_create_initial_roles_and_permissions
        ),
    ] 