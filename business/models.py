import uuid

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

from django_tenants.models import TenantMixin, DomainMixin
from django_tenants.utils import get_public_schema_name

# Create your models here.


class BusinessQuerySet(models.QuerySet):
    def private(self):
        return self.exclude(schema_name=get_public_schema_name())
    

class BusinessTypeChoices(models.TextChoices):
    ECOMMERCE = 'ecommerce'
    FINANCE = 'finance'
    MEDICAL = 'medical'
    SAAS = 'saas'

class Business(TenantMixin):
    # Unique identifier for the business
    company_id = models.UUIDField(
        default=uuid.uuid4, unique=True, db_index=True, primary_key=True
    )

    # Business name
    name = models.CharField(max_length=200, db_index=True)
    business_type = models.CharField(max_length=56, choices=BusinessTypeChoices.choices, blank=True, default="")

    # Instructions for replying to customer requests
    reply_instructions = models.TextField(null=True, blank=True)

    # Address
    address = models.CharField(max_length=256, default="")

    # Contact information (you can add more fields as needed)
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, default="", blank=True)
    contact_person = models.CharField(max_length=100, default="", blank=True)

    # Website URL
    website_url = models.URLField(null=True, blank=True)

    # Industry or category
    industry = models.CharField(max_length=100, default="", blank=True)

    # Token or API key (consider using a more secure method)
    token = models.CharField(max_length=72, null=True, default="")

    # Creation date
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Status (e.g., active, inactive, pending)
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('pending', 'Pending'),
        ],
        default='active',
    )

    # Notes or comments
    notes = models.TextField(null=True, blank=True)

    objects = BusinessQuerySet.as_manager()

    auto_create_schema = True
    auto_drop_schema = True



    def __str__(self):
        return self.name
    
class Domain(DomainMixin):
    pass
        

class Subscription(models.Model):
    # Unique identifier for the subscription
    subscription_id = models.CharField(
        max_length=256, unique=True, db_index=True, primary_key=True
    )

    # Reference to the associated business
    business = models.OneToOneField(
        Business,  # Replace 'yourapp' with your app's name
        on_delete=models.CASCADE,
        related_name='subscription',
    )

    # Subscription plan or type
    plan = models.CharField(max_length=50, default="")

    # Start date of the subscription
    start_date = models.DateField(default=timezone.now)

    # End date of the subscription
    end_date = models.DateField(null=True, blank=True)

    # Monthly subscription cost
    monthly_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )

    def __str__(self):
        return f"{self.business.name} - {self.plan} Subscription"


# class EscalationDepartment(models.Model):
#     name = models.CharField(max_length=50)
#     business = models.ForeignKey(
#         Business, on_delete=models.CASCADE, related_name="escalation_departments",
#     )


# class KnowledgeBase(models.Model):
#     business = models.ForeignKey(
#         Business, on_delete=models.CASCADE, related_name="business_kb", db_index=True
#     )
#     knowledgebase_id = models.CharField(
#         max_length=72, blank=True, null=True, unique=True
#     )
#     title = models.CharField(max_length=125)
#     content = models.CharField(max_length=512)
#     cleaned_data = models.JSONField(default=dict)
#     is_company_description = models.BooleanField(default=False)


# class Reply(models.Model):
#     reply = models.TextField()
#     to_be_escalated = models.BooleanField()
#     sentiment = models.CharField(max_length=20)


# class Category(models.Model):
#     name = models.CharField(max_length=100)

#     def __str__(self):
#         return self.name


# class Product(models.Model):
#     category = models.ForeignKey(Category, on_delete=models.CASCADE)
#     name = models.CharField(max_length=200)
#     description = models.TextField(blank=True)
#     price = models.DecimalField(max_digits=10, decimal_places=2)
#     stock_quantity = models.PositiveIntegerField()
#     image = models.ImageField(upload_to="product_images/", blank=True, null=True)

#     def __str__(self):
#         return self.name


# class Inventory(models.Model):
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     quantity = models.PositiveIntegerField()
#     timestamp = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.product.name} - {self.quantity}"
