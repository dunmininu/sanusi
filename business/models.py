import random
import string
from datetime import datetime, timedelta
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from sanusi_backend.classes.base_model import BaseModel

# from chat.models import Customer
from decimal import Decimal


class BusinessTypeChoices(models.TextChoices):
    FASHION = "fashion"
    SKINCARE = "skincare"
    FOOD = "food"
    ELECTRONICS = "electronics"
    HOME = "home"
    BEAUTY = "beauty"
    KIDS = "kids"
    SPORTS = "sports"
    CRAFTS = "crafts"
    OTHER = "other"
    ECOMMERCE = "ecommerce"
    FINANCE = "finance"
    MEDICAL = "medical"
    SAAS = "saas"


class ProductStatusChoices(models.TextChoices):
    OUT_OF_STOCK = "OUT_OF_STOCK"
    UNAVAILABLE = "UNAVAILABLE"
    AVAILABLE = "AVAILABLE"
    LOW_IN_STOCK = "LOW_IN_STOCK"


CANCELLED = "CANCELLED"
PENDING = "PENDING"
PROCESSING = "PROCESSING"
SHIPPED = "SHIPPED"
DELIVERED = "DELIVERED"


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
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("pending", "Pending"),
        ],
        default="active",
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
        related_name="subscription",
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
        Business,
        on_delete=models.CASCADE,
        related_name="escalation_departments",
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
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
        db_index=True,
    )
    name = models.CharField(max_length=200, db_index=True)
    serial_number = models.CharField(max_length=200, db_index=True, null=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField()
    image = models.URLField(blank=True, null=True)
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="product", db_index=True
    )
    is_active = models.BooleanField(default=True, db_index=True)
    out_of_stock = models.BooleanField(default=False, db_index=True)
    low_in_stock = models.BooleanField(default=False, db_index=True)
    bundle = models.JSONField(default=list)
    tags = models.JSONField(default=list)
    size = models.JSONField(default=list)
    status = models.CharField(
        choices=ProductStatusChoices.choices,
        max_length=60,
        default=ProductStatusChoices.AVAILABLE,
        db_index=True,
    )
    expiry_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name
    

    def generate_serial_number(self):
        def segment(length=3):
            return ''.join(random.choices(string.ascii_uppercase, k=length))

        # Get first 3 uppercase alphanumeric characters of business and product name
        biz_part = ''.join(filter(str.isalnum, self.business.name.upper()))[:3]
        prod_part = ''.join(filter(str.isalnum, self.name.upper()))[:4]

        return f"SN-{biz_part}-{prod_part}-{segment()}-{segment()}-{random.randint(1, 99):02d}"
    
    def save(self, *args, **kwargs):
        if not self.serial_number or self.serial_number.strip() == "":
            self.serial_number = self.generate_serial_number()
        super().save(*args, **kwargs)

    

    def add_to_bundle(self, item, quantity=1):
        """Add one or more items to the bundle"""
        if isinstance(item, list):
            for i in item:
                self._add_single_bundle(i, quantity)
        else:
            self._add_single_bundle(item, quantity)
        self.save(update_fields=["bundle"])

    def _add_single_bundle(self, item, quantity):
        # Since bundle is now always a list, simplify the logic
        if item not in self.bundle:
            self.bundle.append(item)

    def remove_from_bundle(self, item):
        """Remove an item from the bundle"""
        if item in self.bundle:
            self.bundle.remove(item)
        self.save(update_fields=["bundle"])

    def get_bundle_items(self):
        """Get all items in the bundle"""
        return self.bundle or []

    def has_item_in_bundle(self, item):
        """Check if an item is in the bundle"""
        return item in (self.bundle or [])


    

    def add_to_size(self, item, quantity=1):
        """Add one or more items to the size"""
        if isinstance(item, list):
            for i in item:
                self._add_single_size(i, quantity)
        else:
            self._add_single_size(item, quantity)
        self.save(update_fields=["size"])

    def _add_single_size(self, item, quantity):
        # Since bundle is now always a list, simplify the logic
        if item not in self.size:
            self.size.append(item)

    def remove_from_size(self, item):
        """Remove an item from the size"""
        if item in self.bundle:
            self.size.remove(item)
        self.save(update_fields=["size"])

    def get_bundle_items(self):
        """Get all items in the size"""
        return self.size or []

    def has_item_in_bundle(self, item):
        """Check if an item is in the size"""
        return item in (self.size or [])
    
    def add_to_tags(self, item, quantity=1):
        """Add one or more items to the tags"""
        if isinstance(item, list):
            for i in item:
                self._add_single_tags(i, quantity)
        else:
            self._add_single_tags(item, quantity)
        self.save(update_fields=["tags"])

    def _add_single_tags(self, item, quantity):
        # Since bundle is now always a list, simplify the logic
        if item not in self.tags:
            self.tags.append(item)

    def remove_from_tags(self, item):
        """Remove an item from the tags"""
        if item in self.bundle:
            self.tags.remove(item)
        self.save(update_fields=["tags"])

    def get_bundle_items(self):
        """Get all items in the tags"""
        return self.tags or []

    def has_item_in_bundle(self, item):
        """Check if an item is in the tags"""
        return item in (self.tags or [])

    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["business", "serial_number"],
                name="unique_serial_per_business",
            )
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
        (CANCELLED, CANCELLED),
        (PENDING, PENDING),
        (PROCESSING, PROCESSING),
        (SHIPPED, SHIPPED),
        (DELIVERED, DELIVERED),
    )

    # id = models.UUIDField(
    #     default=uuid.uuid4, unique=True, db_index=True, primary_key=True
    # )
    order_id = models.CharField(max_length=20, unique=True, null=False, blank=True)
    delivery_info = models.JSONField()
    payment_summary = models.JSONField()
    delivery_date = models.DateTimeField(default=get_delivery_date, null=True)
    status = models.CharField(choices=STATUSES, max_length=60, default=PENDING)
    customer = models.ForeignKey(
        "chat.Customer",
        on_delete=models.CASCADE,
        related_name="customer_orders",
    )
    platform = models.CharField(max_length=256, null=True, blank=True)
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="order_business", db_index=True
    )
    meta = models.JSONField()

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
        next_number = cls.objects.filter(order_id__startswith="ORD-").count() + 1

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
        vat_amount = Decimal(str(self.payment_summary.get("vat", 0)))

        delivery_fee = Decimal(str(self.payment_summary.get("delivery_fee", 0)))

        # Calculate net_total from all order products
        net_total = sum(item.price * item.quantity for item in self.order_products.all())

        # Ensure net_total is Decimal for accurate calculation
        if not isinstance(net_total, Decimal):
            net_total = Decimal("0")

        # Calculate total (net_total + vat)
        total = net_total + vat_amount + delivery_fee

        # Update payment_summary with calculated values
        self.payment_summary.update(
            {
                "net_total": float(net_total),  # Convert Decimal to float for JSON
                "total": float(total),
                "vat": float(vat_amount),  # Ensure vat is also float
                "delivery_fee": float(delivery_fee),
            }
        )

        # Save the updated payment_summary
        self.save(update_fields=["payment_summary"])

        return {
            "net_total": float(net_total),
            "vat": float(vat_amount),
            "total": float(total),
        }

    class Meta:
        # ordering = ['-last_updated']  # Orders by newest first
        indexes = [
            models.Index(fields=["order_id"]),
            models.Index(fields=["last_updated"]),
        ]

    # Your original (slow)
    # Order.objects.filter(...).order_by('order_id').last()  # O(n log n)

    # Optimized (fast)
    # Order.objects.filter(...).aggregate(Max('order_id'))   # O(1)


class OrderProduct(BaseModel):
    # id = models.UUIDField(
    #     default=uuid.uuid4, unique=True, db_index=True, primary_key=True
    # )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_products")

    class Meta:
        unique_together = [
            "order",
            "product",
        ]  # prevent duplicate products in the same order
