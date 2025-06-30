import os
import json
from django.core.wsgi import get_wsgi_application
from business.models import Category, Product, Inventory

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sanusi_backend.settings")
application = get_wsgi_application()


def create_categories(categories_data):
    for category_data in categories_data:
        Category.objects.create(**category_data)


def create_products(products_data):
    for product_data in products_data:
        category_id = product_data.pop("category_id")
        category = Category.objects.get(id=category_id)
        Product.objects.create(category=category, **product_data)


def create_inventory(inventory_data):
    for inventory_entry in inventory_data:
        product_id = inventory_entry.pop("product_id")
        product = Product.objects.get(id=product_id)
        Inventory.objects.create(product=product, **inventory_entry)


def main():
    with open("inventory.json", "r") as json_file:
        data = json.load(json_file)

        categories_data = data["categories"]
        products_data = data["products"]
        inventory_data = data["inventory"]

        create_categories(categories_data)
        create_products(products_data)
        create_inventory(inventory_data)


if __name__ == "__main__":
    main()
