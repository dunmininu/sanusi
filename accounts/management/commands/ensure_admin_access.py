from django.core.management.base import BaseCommand
from accounts.models import User, Role, Permissions


class Command(BaseCommand):
    help = 'Ensure all users have admin access and required permissions'

    def handle(self, *args, **options):
        try:
            # Get the admin role
            admin_role = Role.objects.get(name='admin')
            self.stdout.write(f'Found admin role: {admin_role.name}')
            
            # Get all users
            users = User.objects.all()
            self.stdout.write(f'Total users: {users.count()}')
            
            # Assign admin role to all users
            updated_count = 0
            for user in users:
                if admin_role not in user.roles.all():
                    user.roles.add(admin_role)
                    updated_count += 1
                    self.stdout.write(f'Assigned admin role to: {user.email}')
            
            self.stdout.write(f'Updated {updated_count} users with admin role')
            
            # Verify permissions
            self.stdout.write('\nVerifying permissions:')
            for user in users:
                has_admin = admin_role in user.roles.all()
                has_customer_create = user.has_module_permission(Permissions.CUSTOMER_CREATE)
                has_customer_view = user.has_module_permission(Permissions.CUSTOMER_VIEW)
                
                self.stdout.write(
                    f'User: {user.email} | '
                    f'Admin: {has_admin} | '
                    f'Customer Create: {has_customer_create} | '
                    f'Customer View: {has_customer_view}'
                )
            
            self.stdout.write(
                self.style.SUCCESS('Successfully ensured all users have admin access!')
            )
            
        except Role.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Admin role not found. Please run setup_roles command first.')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            ) 