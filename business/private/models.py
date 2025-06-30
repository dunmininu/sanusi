from django.db import models

from business.models import Business


class EscalationDepartment(models.Model):
    name = models.CharField(max_length=50)
    # business = models.ForeignKey(
    #     Business, on_delete=models.CASCADE, related_name="escalation_departments",
    # )


class KnowledgeBase(models.Model):
    knowledgebase_id = models.CharField(max_length=72, blank=True, null=True, unique=True)
    title = models.CharField(max_length=125)
    content = models.CharField(max_length=512)
    cleaned_data = models.JSONField(default=dict)
    is_company_description = models.BooleanField(default=False)


class Reply(models.Model):
    reply = models.TextField()
    to_be_escalated = models.BooleanField()
    sentiment = models.CharField(max_length=20)


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField()
    image = models.ImageField(upload_to="product_images/", blank=True, null=True)

    def __str__(self):
        return self.name


class Inventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"
