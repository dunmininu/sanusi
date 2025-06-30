import uuid
from datetime import datetime, timedelta
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from sanusi_backend.classes.base_model import BaseModel
# from chat.models import Customer
from decimal import Decimal


class BusinessTypeChoices(models.TextChoices):
    ECOMMERCE = 'ecommerce'
    FINANCE = 'finance'
    MEDICAL = 'medical'
    SAAS = 'saas'

CANCELLED = 'CANCELLED'
PENDING = 'PENDING'
PROCESSING = 'PROCESSING'
SHIPPED = 'SHIPPED' 
DELIVERED = 'DELIVERED'

def get_delivery_date():
    return datetime.today() + timedelta(days=2)

class Business(BaseModel):
    # Unique identifier for the business
    # company_id = models.UUIDField(
    #     default=uuid.uuid4, unique=True, db_index=True, primary_key=True
    # )

    # Business name
    name = models.CharField(max_length=200, db_index=True)
    business_type = models.CharField(
        max_length=56, choices=BusinessTypeChoices.choices, blank=True, default=""
    )

    # Instructions for replying to customer requests
    reply_instructions = models.TextField(null=True, blank=True)

    # Address
    address = models.CharField(max_length=256, default="")

    # Contact information
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, default="", blank=True)
    contact_person = models.CharField(max_length=100, default="", blank=True)

    # Website URL
    website_url = models.URLField(null=True, blank=True)

    # Industry or category
    industry = models.CharField(max_length=100, default="", blank=True)

    # Token or API key
    token = models.CharField(max_length=72, null=True, default="")

    # Creation date
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Status
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

    def __str__(self):
        return self.name


class Subscription(BaseModel):
    # Unique identifier for the subscription
    # subscription_id = models.UUIDField(
    #     default=uuid.uuid4, unique=True, db_index=True, primary_key=True
    # )

    # Reference to the associated business
    business = models.OneToOneField(
        Business,
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



class EscalationDepartment(BaseModel):
    # id = models.UUIDField(
    #     default=uuid.uuid4, unique=True, db_index=True, primary_key=True
    # )
    name = models.CharField(max_length=50)
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="escalation_departments",
    )


class KnowledgeBase(BaseModel):
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="business_kb", db_index=True
    )
    # knowledgebase_id = models.UUIDField(
    #     default=uuid.uuid4, unique=True, db_index=True, primary_key=True
    # )
    title = models.CharField(max_length=125)
    content = models.CharField(max_length=512)
    cleaned_data = models.JSONField(default=dict)
    is_company_description = models.BooleanField(default=False)


class Reply(BaseModel):
    # id = models.UUIDField(
    #     default=uuid.uuid4, unique=True, db_index=True, primary_key=True
    # )
    reply = models.TextField()
    to_be_escalated = models.BooleanField()
    sentiment = models.CharField(max_length=20)


class Category(BaseModel):
    # id = models.UUIDField(
    #     default=uuid.uuid4, unique=True, db_index=True, primary_key=True
    # )
    name = models.CharField(max_length=100)
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="category", db_index=True
    )

    def __str__(self):
        return self.name


class Product(BaseModel):
    # id = models.UUIDField(
    #     default=uuid.uuid4, unique=True, db_index=True, primary_key=True
    # )
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', db_index=True)
    name = models.CharField(max_length=200)
    serial_number = models.CharField(max_length=200, db_index=True, null=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField()
    image = models.URLField(blank=True, null=True)
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="product", db_index=True
    )
    bundle = models.JSONField(default=dict)

    def __str__(self):
        return self.name
    
    def add_to_bundle(self, item, quantity=1):
        """Add an item to the bundle"""
        if isinstance(self.bundle, dict):
            self.bundle[item] = self.bundle.get(item, 0) + quantity
        elif isinstance(self.bundle, list):
            self.bundle.append(item)
        self.save(update_fields=['bundle'])
    
    def remove_from_bundle(self, item):
        """Remove an item from the bundle"""
        if isinstance(self.bundle, dict) and item in self.bundle:
            del self.bundle[item]
        elif isinstance(self.bundle, list) and item in self.bundle:
            self.bundle.remove(item)
        self.save(update_fields=['bundle'])
    
    def get_bundle_items(self):
        """Get all items in the bundle"""
        if isinstance(self.bundle, dict):
            return list(self.bundle.keys())
        return self.bundle or []
    
    def has_item_in_bundle(self, item):
        """Check if an item is in the bundle"""
        if isinstance(self.bundle, dict):
            return item in self.bundle
        return item in (self.bundle or [])
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['business', 'serial_number'], name='unique_serial_per_business')
        ]


class Inventory(BaseModel):
    # id = models.UUIDField(
    #     default=uuid.uuid4, unique=True, db_index=True, primary_key=True
    # )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"



class Order(BaseModel):
    STATUSES = (
        (CANCELLED, CANCELLED), (PENDING, PENDING), (PROCESSING, PROCESSING),
        (SHIPPED, SHIPPED), (DELIVERED, DELIVERED)
    )

    # id = models.UUIDField(
    #     default=uuid.uuid4, unique=True, db_index=True, primary_key=True
    # )
    order_id = models.CharField(max_length=20, unique=True, null=False, blank=True)
    delivery_info = models.JSONField()
    payment_summary = models.JSONField()
    delivery_date = models.DateTimeField(default=get_delivery_date, null=True)
    status = models.CharField(
        choices=STATUSES, max_length=60, default=PENDING)
    customer = models.ForeignKey(
        'chat.Customer',
        on_delete=models.CASCADE,
        related_name="customer_orders",
    )
    platform = models.CharField(max_length=256, null=True, blank=True)
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="order_business", db_index=True
    )

    def __str__(self):
        return f"{self.order_id} - {self.status}" 

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = self._generate_order_id_simple()
        super().save(*args, **kwargs)

    @classmethod 
    def _generate_order_id_simple(cls):
        """
        Simplified version using database row counting.
        Good balance between performance and simplicity.
        """
        # Count existing orders + 1 (handles deletions better than max)
        next_number = cls.objects.filter(
            order_id__startswith='ORD-'
        ).count() + 1
        
        # Handle edge case where count might not reflect actual max number
        while cls.objects.filter(order_id=f"ORD-{next_number:03d}").exists():
            next_number += 1
            
        return f"ORD-{next_number:03d}"

    def product_count(self):
        return self.order_products.count()


    def aggregate(self):
        """
        Calculate net_total and total from order products and update payment_summary.
        Gets VAT from existing payment_summary, calculates net_total from order products,
        then calculates total (net_total + vat) and updates payment_summary.
        """
        
        # Get existing VAT from payment_summary (default to 0 if not present)
        vat_amount = Decimal(str(self.payment_summary.get('vat', 0)))

        delivery_fee = Decimal(str(self.payment_summary.get('delivery_fee', 0)))
        
        # Calculate net_total from all order products
        net_total = sum(
            item.price * item.quantity 
            for item in self.order_products.all()
        )
        
        # Ensure net_total is Decimal for accurate calculation
        if not isinstance(net_total, Decimal):
            net_total = Decimal('0')
        
        # Calculate total (net_total + vat)
        total = net_total + vat_amount + delivery_fee
        
        # Update payment_summary with calculated values
        self.payment_summary.update({
            'net_total': float(net_total),  # Convert Decimal to float for JSON
            'total': float(total),
            'vat': float(vat_amount),  # Ensure vat is also float
            'delivery_fee': float(delivery_fee)
        })
        
        # Save the updated payment_summary
        self.save(update_fields=['payment_summary'])
        
        return {
            'net_total': float(net_total),
            'vat': float(vat_amount),
            'total': float(total)
        }
    
    class Meta:
        # ordering = ['-last_updated']  # Orders by newest first
        indexes = [
            models.Index(fields=['order_id']),
            models.Index(fields=['last_updated']),
        ]


    # Your original (slow)
    # Order.objects.filter(...).order_by('order_id').last()  # O(n log n)

    # Optimized (fast) 
    #Order.objects.filter(...).aggregate(Max('order_id'))   # O(1)

class OrderProduct(BaseModel):
    # id = models.UUIDField(
    #     default=uuid.uuid4, unique=True, db_index=True, primary_key=True
    # )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_products')
    meta = models.JSONField()

    class Meta:
        unique_together = ['order', 'product'] # prevent duplicate products in the same order

