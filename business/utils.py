from typing import Optional, List
from django.contrib.auth import get_user_model
from .models import Business

User = get_user_model()


def get_business_owner(business: Business) -> Optional[User]:
    """
    Get the owner of a business.
    
    Args:
        business: The business instance
        
    Returns:
        User instance if owner exists, None otherwise
    """
    return business.owner


def is_business_owner(user: User, business: Business) -> bool:
    """
    Check if a user is the owner of a business.
    
    Args:
        user: The user to check
        business: The business to check ownership for
        
    Returns:
        True if user is the owner, False otherwise
    """
    return business.owner == user


def get_user_businesses(user: User) -> List[Business]:
    """
    Get all businesses owned by a user.
    
    Args:
        user: The user to get businesses for
        
    Returns:
        List of Business instances owned by the user
    """
    return Business.objects.filter(owner=user)


def get_user_owned_business_ids(user: User) -> List[str]:
    """
    Get all business IDs owned by a user.
    
    Args:
        user: The user to get business IDs for
        
    Returns:
        List of business IDs (strings) owned by the user
    """
    return list(Business.objects.filter(owner=user).values_list('id', flat=True))


def ensure_business_owner_permissions(user: User, business: Business) -> bool:
    """
    Ensure a business owner has all necessary permissions.
    
    Args:
        user: The user to check/update
        business: The business to check ownership for
        
    Returns:
        True if user is owner and has permissions, False otherwise
    """
    if not is_business_owner(user, business):
        return False
    
    # Import here to avoid circular imports
    from accounts.models import Role, Permissions
    
    # Get admin role
    try:
        admin_role = Role.objects.get(name='admin')
        
        # Ensure business owner has admin role
        if admin_role not in user.roles.all():
            user.roles.add(admin_role)
            return True
        
        return True
    except Role.DoesNotExist:
        return False


def get_business_owners() -> List[User]:
    """
    Get all users who own at least one business.
    
    Returns:
        List of User instances who are business owners
    """
    return User.objects.filter(owned_businesses__isnull=False).distinct()


def get_business_by_owner_email(email: str) -> Optional[Business]:
    """
    Get a business by owner's email address.
    
    Args:
        email: The email address of the business owner
        
    Returns:
        Business instance if found, None otherwise
    """
    try:
        return Business.objects.get(owner__email=email)
    except Business.DoesNotExist:
        return None


def get_businesses_by_owner_email(email: str) -> List[Business]:
    """
    Get all businesses owned by a user with the given email.
    
    Args:
        email: The email address of the business owner
        
    Returns:
        List of Business instances owned by the user
    """
    return Business.objects.filter(owner__email=email) 