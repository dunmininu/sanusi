from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.cache import CachedUserPermissionManager, PermissionCache
from accounts.models import Permissions
import time

User = get_user_model()


class Command(BaseCommand):
    help = 'Test the permission caching system'

    def add_arguments(self, parser):
        parser.add_argument('--user-email', type=str, help='Email of user to test')
        parser.add_argument('--clear-cache', action='store_true', help='Clear all permission cache')

    def handle(self, *args, **options):
        if options['clear_cache']:
            self.stdout.write('Clearing all permission cache...')
            PermissionCache.clear_all_permission_cache()
            self.stdout.write(self.style.SUCCESS('Cache cleared successfully!'))
            return

        if not options['user_email']:
            self.stdout.write(self.style.ERROR('Please provide a user email with --user-email'))
            return

        try:
            user = User.objects.get(email=options['user_email'])
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with email {options["user_email"]} not found'))
            return

        self.stdout.write(f'Testing permission cache for user: {user.email}')
        self.stdout.write('=' * 50)

        # Test 1: Basic permission checks
        self.stdout.write('Test 1: Basic permission checks')
        start_time = time.time()
        has_chat_view = CachedUserPermissionManager.has_permission(user, Permissions.CHAT_VIEW)
        has_product_view = CachedUserPermissionManager.has_permission(user, Permissions.PRODUCT_VIEW)
        has_admin = CachedUserPermissionManager.has_permission(user, Permissions.SYSTEM_ADMIN)
        end_time = time.time()
        
        self.stdout.write(f'  - Can view chat: {has_chat_view}')
        self.stdout.write(f'  - Can view products: {has_product_view}')
        self.stdout.write(f'  - Is admin: {has_admin}')
        self.stdout.write(f'  - Time taken: {end_time - start_time:.4f} seconds')

        # Test 2: Role checks
        self.stdout.write('\nTest 2: Role checks')
        start_time = time.time()
        is_admin = CachedUserPermissionManager.is_admin(user)
        is_sales_agent = CachedUserPermissionManager.is_sales_agent(user)
        is_inventory_admin = CachedUserPermissionManager.is_inventory_admin(user)
        end_time = time.time()
        
        self.stdout.write(f'  - Is admin: {is_admin}')
        self.stdout.write(f'  - Is sales agent: {is_sales_agent}')
        self.stdout.write(f'  - Is inventory admin: {is_inventory_admin}')
        self.stdout.write(f'  - Time taken: {end_time - start_time:.4f} seconds')

        # Test 3: Capability checks
        self.stdout.write('\nTest 3: Capability checks')
        start_time = time.time()
        can_access_chat = CachedUserPermissionManager.can_access_chat(user)
        can_respond_to_chat = CachedUserPermissionManager.can_respond_to_chat(user)
        can_view_orders = CachedUserPermissionManager.can_view_orders(user)
        can_process_orders = CachedUserPermissionManager.can_process_orders(user)
        can_view_products = CachedUserPermissionManager.can_view_products(user)
        can_edit_products = CachedUserPermissionManager.can_edit_products(user)
        can_manage_inventory = CachedUserPermissionManager.can_manage_inventory(user)
        end_time = time.time()
        
        self.stdout.write(f'  - Can access chat: {can_access_chat}')
        self.stdout.write(f'  - Can respond to chat: {can_respond_to_chat}')
        self.stdout.write(f'  - Can view orders: {can_view_orders}')
        self.stdout.write(f'  - Can process orders: {can_process_orders}')
        self.stdout.write(f'  - Can view products: {can_view_products}')
        self.stdout.write(f'  - Can edit products: {can_edit_products}')
        self.stdout.write(f'  - Can manage inventory: {can_manage_inventory}')
        self.stdout.write(f'  - Time taken: {end_time - start_time:.4f} seconds')

        # Test 4: Get all permissions and roles
        self.stdout.write('\nTest 4: Get all permissions and roles')
        start_time = time.time()
        permissions = CachedUserPermissionManager.get_user_permissions(user)
        roles = CachedUserPermissionManager.get_user_roles(user)
        end_time = time.time()
        
        self.stdout.write(f'  - User permissions ({len(permissions)}): {permissions[:5]}{"..." if len(permissions) > 5 else ""}')
        self.stdout.write(f'  - User roles ({len(roles)}): {roles}')
        self.stdout.write(f'  - Time taken: {end_time - start_time:.4f} seconds')

        # Test 5: Multiple permission checks (simulating API calls)
        self.stdout.write('\nTest 5: Multiple permission checks (simulating API calls)')
        start_time = time.time()
        for i in range(100):
            CachedUserPermissionManager.has_permission(user, Permissions.CHAT_VIEW)
            CachedUserPermissionManager.has_permission(user, Permissions.PRODUCT_VIEW)
            CachedUserPermissionManager.can_access_chat(user)
            CachedUserPermissionManager.can_view_products(user)
        end_time = time.time()
        
        self.stdout.write(f'  - 400 permission checks completed')
        self.stdout.write(f'  - Time taken: {end_time - start_time:.4f} seconds')
        self.stdout.write(f'  - Average time per check: {(end_time - start_time) / 400:.6f} seconds')

        # Test 6: Cache invalidation
        self.stdout.write('\nTest 6: Cache invalidation')
        self.stdout.write('  - Invalidating user cache...')
        CachedUserPermissionManager.invalidate_user_cache(user)
        self.stdout.write('  - Cache invalidated successfully')

        # Test 7: Performance comparison (with and without cache)
        self.stdout.write('\nTest 7: Performance comparison')
        
        # Without cache (direct database queries)
        start_time = time.time()
        for i in range(50):
            user.has_module_permission(Permissions.CHAT_VIEW)
            user.has_module_permission(Permissions.PRODUCT_VIEW)
        end_time = time.time()
        db_time = end_time - start_time
        
        # With cache
        start_time = time.time()
        for i in range(50):
            CachedUserPermissionManager.has_permission(user, Permissions.CHAT_VIEW)
            CachedUserPermissionManager.has_permission(user, Permissions.PRODUCT_VIEW)
        end_time = time.time()
        cache_time = end_time - start_time
        
        self.stdout.write(f'  - Database queries time: {db_time:.4f} seconds')
        self.stdout.write(f'  - Cached queries time: {cache_time:.4f} seconds')
        if db_time > 0:
            improvement = ((db_time - cache_time) / db_time) * 100
            self.stdout.write(f'  - Performance improvement: {improvement:.1f}%')

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('Permission cache testing completed!')) 