from django.core.management.base import BaseCommand
from business.models import Business
from accounts.models import User, Role, Permissions


class Command(BaseCommand):
    help = 'Assign owners to businesses and ensure business owners have admin access'

    def add_arguments(self, parser):
        parser.add_argument(
            '--assign-first-user',
            action='store_true',
            help='Assign the first user as owner to all businesses without owners',
        )
        parser.add_argument(
            '--ensure-admin-access',
            action='store_true',
            help='Ensure all business owners have admin access',
        )

    def handle(self, *args, **options):
        try:
            # Get admin role
            admin_role = Role.objects.get(name='admin')
            self.stdout.write(f'Found admin role: {admin_role.name}')
            
            # Get all businesses
            businesses = Business.objects.all()
            self.stdout.write(f'Total businesses: {businesses.count()}')
            
            # Assign owners if requested
            if options['assign_first_user']:
                users = User.objects.all()
                if users.exists():
                    first_user = users.first()
                    self.stdout.write(f'Using first user as owner: {first_user.email}')
                    
                    # Assign first user to businesses without owners
                    businesses_without_owners = businesses.filter(owner__isnull=True)
                    updated_count = 0
                    
                    for business in businesses_without_owners:
                        business.owner = first_user
                        business.save()
                        updated_count += 1
                        self.stdout.write(f'Assigned {first_user.email} as owner of: {business.name}')
                    
                    self.stdout.write(f'Updated {updated_count} businesses with owner')
                else:
                    self.stdout.write(self.style.ERROR('No users found to assign as owners'))
            
            # Ensure business owners have admin access
            if options['ensure_admin_access']:
                business_owners = User.objects.filter(owned_businesses__isnull=False).distinct()
                self.stdout.write(f'Found {business_owners.count()} business owners')
                
                updated_count = 0
                for owner in business_owners:
                    if admin_role not in owner.roles.all():
                        owner.roles.add(admin_role)
                        updated_count += 1
                        self.stdout.write(f'Assigned admin role to business owner: {owner.email}')
                
                self.stdout.write(f'Updated {updated_count} business owners with admin role')
            
            # Display current business ownership
            self.stdout.write('\nCurrent business ownership:')
            for business in businesses:
                owner_info = f'{business.owner.email}' if business.owner else 'No owner'
                self.stdout.write(f'Business: {business.name} | Owner: {owner_info}')
            
            # Verify permissions for business owners
            self.stdout.write('\nVerifying business owner permissions:')
            business_owners = User.objects.filter(owned_businesses__isnull=False).distinct()
            for owner in business_owners:
                has_admin = admin_role in owner.roles.all()
                has_customer_create = owner.has_module_permission(Permissions.CUSTOMER_CREATE)
                has_business_update = owner.has_module_permission(Permissions.BUSINESS_UPDATE)
                
                self.stdout.write(
                    f'Owner: {owner.email} | '
                    f'Admin: {has_admin} | '
                    f'Customer Create: {has_customer_create} | '
                    f'Business Update: {has_business_update}'
                )
            
            self.stdout.write(
                self.style.SUCCESS('Successfully processed business ownership!')
            )
            
        except Role.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Admin role not found. Please run setup_roles command first.')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            ) 