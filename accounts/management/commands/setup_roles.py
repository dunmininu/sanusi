from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Role, ModulePermission, Permissions, Roles

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up initial roles and permissions for the system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            help='Email of user to assign admin role to',
        )
        parser.add_argument(
            '--create-admin',
            action='store_true',
            help='Create a default admin user if none exists',
        )

    def handle(self, *args, **options):
        self.stdout.write('Setting up roles and permissions...')
        
        # Create permissions if they don't exist
        self.create_permissions()
        
        # Create roles
        self.create_roles()
        
        # Assign admin role to user if specified
        if options['user_email']:
            self.assign_admin_role(options['user_email'])
        
        # Create default admin if requested
        if options['create_admin']:
            self.create_default_admin()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up roles and permissions!')
        )

    def create_permissions(self):
        """Create all permissions if they don't exist."""
        self.stdout.write('Creating permissions...')
        
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
        
        created_count = 0
        for code, name, description, module in permissions_data:
            permission, created = ModulePermission.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'description': description,
                    'module': module,
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'  Created permission: {name}')
        
        self.stdout.write(f'Created {created_count} new permissions')

    def create_roles(self):
        """Create the three main roles with their permissions."""
        self.stdout.write('Creating roles...')
        
        # Create Admin role
        admin_role, created = Role.objects.get_or_create(
            name=Roles.ADMIN,
            defaults={
                'description': 'Full system access with all permissions',
                'is_system_role': True,
                'is_active': True,
            }
        )
        if created:
            self.stdout.write('  Created Admin role')
        
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
        if created:
            self.stdout.write('  Created Sales Agent role')
        
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
        if created:
            self.stdout.write('  Created Inventory Admin role')
        
        # Inventory Admin permissions (Sales Agent + Product management)
        inventory_admin_permissions = sales_agent_permissions + [
            'product.create', 'product.update', 'product.delete', 'product.manage_inventory',
        ]
        
        inventory_admin_perms = ModulePermission.objects.filter(
            code__in=inventory_admin_permissions,
            is_active=True
        )
        inventory_admin_role.permissions.set(inventory_admin_perms)
        
        self.stdout.write('Successfully created all roles with their permissions')

    def assign_admin_role(self, email):
        """Assign admin role to a user by email."""
        try:
            user = User.objects.get(email=email)
            admin_role = Role.objects.get(name=Roles.ADMIN)
            user.roles.add(admin_role)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully assigned admin role to {email}')
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with email {email} does not exist')
            )
        except Role.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Admin role does not exist')
            )

    def create_default_admin(self):
        """Create a default admin user if none exists."""
        if User.objects.filter(roles__name=Roles.ADMIN).exists():
            self.stdout.write('Admin user already exists')
            return
        
        # Create default admin user
        admin_email = 'admin@sanusi.com'
        admin_password = 'admin123'  # This should be changed immediately
        
        try:
            admin_user = User.objects.create_user(
                email=admin_email,
                password=admin_password,
                first_name='Admin',
                last_name='User',
                is_staff=True,
            )
            
            admin_role = Role.objects.get(name=Roles.ADMIN)
            admin_user.roles.add(admin_role)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created default admin user: {admin_email} / {admin_password}'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    'Please change the default admin password immediately!'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to create default admin: {e}')
            ) 