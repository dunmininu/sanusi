import json
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from .models import (
    Business,
    KnowledgeBase,
    EscalationDepartment,
    Product,
    Category,
    OrderProduct,
    Order,
)
from chat.models import Customer

# from business.private.models import KnowledgeBase, EscalationDepartment
from sanusi.views import generate_response_chat
from sanusi_backend.utils.error_handler import ErrorHandler
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeBase
        fields = [
            "title",
            "content",
            "id",
            "is_company_description",
            "cleaned_data",
        ]
        extra_kwargs = {"cleaned_data": {"read_only": True}}

    def create(self, validated_data):
        title = validated_data["title"]
        content = validated_data["content"]
        knowledgebase_id = validated_data["knowledgebase_id"]
        is_company_description = validated_data["is_company_description"]
        company_id = self.context.get("company_id")

        business = get_object_or_404(Business, id=company_id)

        prompt = [
            {
                "role": "system",
                "content": (
                    "Clean this data into a reusable json content that openai chat can understand "
                    "and use for response processing later not more than 512 characters"
                ),
            },
            {
                "role": "user",
                "content": f"data to be cleaned {content}",
            },
        ]
        response = generate_response_chat(prompt, 400)

        try:
            cleaned_data = json.dumps(response["choices"][0]["message"]["content"])
        except Exception as e:
            print("An error occurred:", str(e))
            cleaned_data = response["choices"][0]["message"]["content"]

        kb = KnowledgeBase.objects.create(
            title=title,
            content=content,
            id=knowledgebase_id,
            is_company_description=is_company_description,
            cleaned_data=cleaned_data,
            business=business,
        )

        return kb


class BulkCreateKnowledgeBaseSerializer(serializers.ListSerializer):
    child = KnowledgeBaseSerializer()

    def create(self, validated_data):
        knowledge_bases = []
        for item in validated_data:
            kb_serializer = KnowledgeBaseSerializer(data=item, context=self.context)
            if kb_serializer.is_valid():
                knowledge_base = kb_serializer.save()
                knowledge_bases.append(knowledge_base)
        return knowledge_bases


class KnowledgeBaseDeleteSerializer(serializers.Serializer):
    knowledgebase_id = serializers.CharField(required=False, allow_null=True)


class KnowledgeBaseBulkUpdateSerializer(serializers.ListSerializer):
    child = KnowledgeBaseSerializer()


class EscalationDepartmentSeralizer(serializers.ModelSerializer):
    class Meta:
        model = EscalationDepartment
        fields = ["name"]


class BusinessSerializer(serializers.ModelSerializer):
    escalation_departments = EscalationDepartmentSeralizer(many=True)
    knowledge_base = serializers.SerializerMethodField()

    class Meta:
        model = Business
        fields = [
            "name",
            "id",
            "address",
            "email",
            "phone_number",
            "escalation_departments",
            "reply_instructions",
            "knowledge_base",
            "business_type",
        ]
        read_only_fields = ["id"]

    def get_knowledge_base(self, business):
        knowledge_base = KnowledgeBase.objects.filter(
            business=business, is_company_description=True
        ).first()
        return KnowledgeBaseSerializer(knowledge_base).data if knowledge_base else None

    def validate(self, data):
        """
        Validate the serializer data before creating the Business instance.
        """
        # Check if company_id is provided
        company_id = data.get("company_id")
        # Check if company_id already exists
        if Business.objects.filter(id=company_id).exists():
            ErrorHandler.validation_error(
                    message="Company ID already exists",
                    field="id", 
                    error_code="INVALID_COMPANY_ID",
                    extra_data={"provided_id": data["company_id"]}
                )
        return data

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        escalation_departments_data = validated_data.pop("escalation_departments")
        business = Business.objects.create(**validated_data)

        # Check if this will be the user's first business
        is_first_business = not user.businesses.exists()

        user.businesses.add(business)

        # Set as default only if it's the first business
        if is_first_business:
            user.set_default_business(business)

        for department_data in escalation_departments_data:
            EscalationDepartment.objects.create(business=business, **department_data)

        return business

    def update(self, instance, validated_data):
        escalation_departments_data = validated_data.pop("escalation_departments", None)
        instance.name = validated_data.get("name", instance.name)
        instance.email = validated_data.get("email", instance.email)
        instance.reply_instructions = validated_data.get(
            "reply_instructions", instance.reply_instructions
        )
        instance.save()

        if escalation_departments_data is not None:
            # delete old departments
            instance.escalation_departments.all().delete()
            # create new departments
            for department_data in escalation_departments_data:
                EscalationDepartment.objects.create(business=instance, **department_data)

        return instance


class SanusiBusinessCreateSerializer(serializers.Serializer):
    company_id = serializers.CharField(required=False, allow_null=True)
    business_name = serializers.CharField(required=False, allow_null=True)
    knowledge_base = serializers.ListField(required=False, allow_null=True)
    instructions = serializers.CharField(required=False, allow_null=True)
    escalation_departments = serializers.ListField(required=False, allow_null=True)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "business"]
        read_only_fields = ["id","business"]  # Prevent user from manually setting it
    
    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        default_business = user.get_default_business()
        if not default_business:
            ErrorHandler.validation_error(
                message="User does not have a business.",
                field="business_id", 
                error_code="NO_DEFAULT_BUSINESS",
                extra_data={"user_id": user.id}
            )
      
        category = Category(**validated_data)
        category.business = default_business
        category.save()
        
        return category



class InventorySerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    business = BusinessSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=True,
        source="category",
    )  # For POST/PUT
    class Meta:
        model = Product
        fields = [
            "id", 
            "name", 
            "business", 
            "category", 
            "serial_number", 
            "description", 
            "price", 
            "stock_quantity", 
            "image", 
            "bundle", 
            "category_id", 
            "status"
        ]
        read_only_fields = ["id","business"]  # Prevent user from manually setting it


    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        default_business = user.get_default_business()
        bundles_data = validated_data.pop("bundles", None)
        price_data = validated_data.pop("price", None)
        if not default_business:
            ErrorHandler.validation_error(
                message="User does not have a business.",
                field="business_id",
                error_code="NO_DEFAULT_BUSINESS",
                extra_data={"user_id": user.id},
            )

        if not price_data:
            ErrorHandler.validation_error(
                message="User does not have price.",
                field="price",
                error_code="NO_DEFAULT_PRODUCT_PRICE",
                extra_data={"user_id": user.id},
            )

        # Convert price to decimal with 2 decimal places
        try:
            # Ensure we're working with numeric type
            price_value = Decimal(str(price_data))
            # Round to 2 decimal places using standard rounding
            price_value = price_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except (TypeError, ValueError, InvalidOperation) as e:
            ErrorHandler.validation_error(
                message=f"Invalid price format: {str(e)}",
                field="price",
                error_code="INVALID_PRICE_FORMAT",
                extra_data={"price_data": price_data},
            )

        product = Product(**validated_data)
        product.business = default_business
        product.price = price_value
        product.save()
        if bundles_data is not None:
            product.add_to_bundle(bundles_data)
        return product

    def update(self, instance, validated_data):
        self.context.get("request")
        bundles_data = validated_data.pop("bundles", None)
        price_data = validated_data.get("price")

        # Handle price conversion if provided
        if price_data is not None:
            try:
                price_value = Decimal(str(price_data))
                price_value = price_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                validated_data["price"] = price_value
            except (TypeError, ValueError, InvalidOperation) as e:
                ErrorHandler.validation_error(
                    message=f"Invalid price format: {str(e)}",
                    field="price",
                    error_code="INVALID_PRICE_FORMAT",
                    extra_data={"price_data": price_data},
                )

        # Update instance fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if bundles_data is not None:
            instance.add_to_bundle(bundles_data)

        return instance




class OrderProductSerializer(serializers.ModelSerializer):
    product = InventorySerializer(read_only=True)  # Complete product details
    product_id = serializers.UUIDField(write_only=True)  # For creating/updating

    class Meta:
        model = OrderProduct
        fields = [
            "id", 
            "product", 
            "product_id", 
            "quantity", 
            "price"
        ]
        read_only_fields = ["id"]


class CustomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "id", 
            "name", 
            "email", 
            "phone_number", 
            "platform", 
            "identifier", 
            "business", 
            "date_created"
        ]
        read_only_fields = [
            "id",
            "identifier", 
            "business", 
            "date_created"
        ]  # Prevent user from manually setting it

class OrderSerializer(serializers.ModelSerializer):
    order_products = OrderProductSerializer(
        many=True, read_only=True
    )  # Complete order products
    customer = CustomeSerializer(read_only=True)  # Complete customer details
    customer_id = serializers.UUIDField(write_only=True)  # For creating/updating
    order_products_data = serializers.ListField(
        child=serializers.DictField(), write_only=True, required=False
    )
    business = BusinessSerializer(read_only=True)  # Complete business details

    class Meta:
        model = Order
        fields = [
            "id",
            "order_id",
            "delivery_info",
            "payment_summary",
            "meta",
            "delivery_date",
            "status",
            "customer_id",
            "business",
            "customer",
            "order_products",
            "order_products_data",
            "date_created",
            "last_updated",
        ]
        read_only_fields = [
            "id",
            "order_id",
            "business",
            "date_created",
            "last_updated",
            "customer",
        ]

    def _validate_and_reserve_inventory(self, order_products_data, business):
        """
        Validate product availability and reserve inventory
        """
        inventory_updates = []

        for product_data in order_products_data:
            product_id = product_data.get("product_id")
            stock_quantity = product_data.get("quantity", 0)
            price = product_data.get("price", 0)

            try:
                product = Product.objects.select_for_update().get(
                    id=product_id, business=business
                )
            except Product.DoesNotExist:
                ErrorHandler.validation_error(
                    message="Product not found or doesn't belong to this business.",
                    field="product_id",
                    error_code="INVALID_PRODUCT",
                    extra_data={"product_id": product_id, "business_id": business},
                )

            # Check if there's enough inventory
            if product.stock_quantity < stock_quantity:
                ErrorHandler.validation_error(
                    message=(
                        f"Insufficient inventory for product '{product.name}'. Available: "
                        f"{product.stock_quantity}, Requested: {stock_quantity}"
                    ),
                    field="stock_quantity",
                    error_code="INSUFFICIENT_INVENTORY",
                    extra_data={
                        "product_id": product_id,
                        "available_quantity": product.stock_quantity,
                        "requested_quantity": stock_quantity,
                    },
                )

            # Check if there's enough inventory
            if product.price > price:
                ErrorHandler.validation_error(
                    message=(
                        f"Invalid price for product '{product.name}'. "
                        f"Product price: {product.price}, Requested price: {price}"
                    ),
                    field="price",
                    error_code="INVALID_PRICE",
                    extra_data={
                        "product_id": product_id,
                        "product_price": product.price,
                        "requested_price": price,
                    },
                )

            # Store for inventory update
            inventory_updates.append(
                {"product": product, "quantity_to_deduct": stock_quantity}
            )

        return inventory_updates

    def _update_inventory(self, inventory_updates, operation="deduct"):
        """
        Update product inventory quantities
        operation: 'deduct' or 'restore'
        """
        for update in inventory_updates:
            product = update["product"]
            stock_quantity = update["quantity_to_deduct"]
            if operation == "deduct":
                product.stock_quantity -= stock_quantity
                print("product.stock_quantity2", product.stock_quantity)
            elif operation == "restore":
                product.stock_quantity += stock_quantity

            # Ensure quantity doesn't go below 0
            if product.stock_quantity < 0:
                product.stock_quantity = 0

            product.save(update_fields=["stock_quantity"])
            print("deduct :", product)

    def _restore_inventory_from_order_products(self, order_products, business):
        """
        Restore inventory from existing order products (used when cancelling orders)
        """
        for order_product in order_products:
            product = order_product.product
            stock_quantity = order_product.quantity

            product.stock_quantity += stock_quantity
            product.save(update_fields=["stock_quantity"])

    # @transaction.atomic
    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        default_business = user.get_default_business()

        if not default_business:
            ErrorHandler.validation_error(
                message="User does not have a business.",
                field="business_id",
                error_code="NO_DEFAULT_BUSINESS",
                extra_data={"user_id": user.id},
            )

        # Extract nested data
        order_products_data = validated_data.pop("order_products_data", [])
        customer_id = validated_data.pop("customer_id")

        # Validate customer belongs to business
        try:
            customer = Customer.objects.get(id=customer_id, business=default_business)
        except Customer.DoesNotExist:
            ErrorHandler.validation_error(
                message="Customer not found or doesn't belong to this business.",
                field="customer_id",
                error_code="INVALID_CUSTOMER",
                extra_data={
                    "customer_id": customer_id,
                    "business_id": default_business,
                },
            )

        # Validate inventory and prepare for deduction
        inventory_updates = self._validate_and_reserve_inventory(
            order_products_data, default_business
        )

        # Create order
        order = Order.objects.create(
            customer=customer, business=default_business, **validated_data
        )

        # Create order products and update inventory
        try:
            for i, product_data in enumerate(order_products_data):
                product_data.get("product_id")
                quantity = product_data.get("quantity")
                price = product_data.get("price")
                # meta = product_data.get("meta", {})

                # Get the validated product from inventory_updates
                product = inventory_updates[i]["product"]

                # Convert price to decimal
                try:
                    price_value = Decimal(str(price))
                    price_value = price_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                except (TypeError, ValueError, InvalidOperation) as e:
                    ErrorHandler.validation_error(
                        message=f"Invalid price format: {str(e)}",
                        field="price",
                        error_code="INVALID_PRICE_FORMAT",
                        extra_data={"price_data": price},
                    )

                OrderProduct.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=price_value,
                    # meta=meta,
                )

            # Update inventory (deduct quantities)
            self._update_inventory(inventory_updates, operation="deduct")

        except Exception as e:
            # If anything goes wrong, the transaction will rollback
            ErrorHandler.log_and_raise(
                message=f"Unexpected error creating order: {str(e)}",
                error_code="UNEXPECTED_ERROR",
                status_code=500,
                log_level="critical",
                extra_data={
                    "exception_type": type(e).__name__,
                    "user_id": str(request.user.id),
                },
            )

        # Aggregate order totals
        order.aggregate()

        return order

    # @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context.get("request")
        user = request.user
        default_business = user.get_default_business()

        # Store original status for comparison
        original_status = instance.status
        new_status = validated_data.get("status", original_status)

        # Extract nested data
        order_products_data = validated_data.pop("order_products_data", None)
        customer_id = validated_data.pop("customer_id", None)

        # Update customer if provided
        if customer_id:
            try:
                customer = Customer.objects.get(id=customer_id, business=default_business)

                instance.customer = customer
            except Customer.DoesNotExist:
                ErrorHandler.validation_error(
                    message="Customer not found or doesn't belong to this business.",
                    field="customer_id",
                    error_code="INVALID_CUSTOMER",
                    extra_data={
                        "customer_id": customer_id,
                        "business_id": default_business,
                    },
                )

        # Handle status change to CANCELLED - restore inventory
        if original_status != "CANCELLED" and new_status == "CANCELLED":
            # Restore inventory from existing order products
            existing_order_products = instance.order_products.select_related("product").all()
            self._restore_inventory_from_order_products(
                existing_order_products, default_business
            )

        # Handle status change from CANCELLED to active status - deduct inventory again
        elif original_status == "CANCELLED" and new_status != "CANCELLED":
            if order_products_data:
                # Validate and reserve inventory for new products
                inventory_updates = self._validate_and_reserve_inventory(
                    order_products_data, default_business
                )
            else:
                # Use existing order products
                order_products_data_from_existing = []
                for op in instance.order_products.all():
                    order_products_data_from_existing.append(
                        {
                            "product_id": str(op.product.id),
                            "quantity": op.quantity,
                            "price": op.price,
                            # "meta": op.meta,
                        }
                    )
                inventory_updates = self._validate_and_reserve_inventory(
                    order_products_data_from_existing, default_business
                )

            # Deduct inventory
            self._update_inventory(inventory_updates, operation="deduct")

        # Update order fields
        # Fields that should be merged instead of overwritten
        json_merge_fields = ['delivery_info', 'payment_summary', 'meta']

        for attr, value in validated_data.items():
            if attr in json_merge_fields:
                current_value = getattr(instance, attr, {}) or {}
                if isinstance(current_value, dict) and isinstance(value, dict):
                    current_value.update(value)  # merge new values into existing
                    setattr(instance, attr, current_value)
                else:
                    setattr(instance, attr, value)  # fallback if not dicts
            else:
                setattr(instance, attr, value)


        instance.save()

        # Update order products if provided (and not just changing to/from cancelled)
        if order_products_data is not None and original_status != "CANCELLED":
            # If order is currently active, restore inventory from old products first
            if new_status != "CANCELLED":
                existing_order_products = instance.order_products.select_related(
                    "product"
                ).all()
                self._restore_inventory_from_order_products(
                    existing_order_products, default_business
                )

            # Clear existing order products
            instance.order_products.all().delete()

            # Create new order products
            if new_status != "CANCELLED":  # Only create new products if not cancelled
                inventory_updates = self._validate_and_reserve_inventory(
                    order_products_data, default_business
                )

                for i, product_data in enumerate(order_products_data):
                    product_data.get("product_id")
                    quantity = product_data.get("quantity")
                    price = product_data.get("price")
                    # meta = product_data.get("meta", {})

                    # Get the validated product from inventory_updates
                    product = inventory_updates[i]["product"]

                    # Convert price to decimal
                    try:
                        price_value = Decimal(str(price))
                        price_value = price_value.quantize(
                            Decimal("0.01"), rounding=ROUND_HALF_UP
                        )
                    except (TypeError, ValueError, InvalidOperation) as e:
                        ErrorHandler.validation_error(
                            message=f"Invalid price format: {str(e)}",
                            field="price",
                            error_code="INVALID_PRICE_FORMAT",
                            extra_data={"price_data": price},
                        )

                    OrderProduct.objects.create(
                        order=instance,
                        product=product,
                        quantity=quantity,
                        price=price_value,
                        # meta=meta,
                    )

                # Update inventory (deduct quantities for new products)
                self._update_inventory(inventory_updates, operation="deduct")

            # Re-aggregate order totals
            instance.aggregate()

        return instance

    # def create(self, validated_data):
    #     request = self.context.get("request")
    #     user = request.user
    #     default_business = user.get_default_business()

    #     if not default_business:
    #         ErrorHandler.validation_error(
    #             message="User does not have a business.",
    #             field="business_id",
    #             error_code="NO_DEFAULT_BUSINESS",
    #             extra_data={"user_id": user.id}
    #         )

    #     # Extract nested data
    #     order_products_data = validated_data.pop("order_products_data", [])
    #     customer_id = validated_data.pop("customer_id")

    #     # Validate customer belongs to business
    #     try:
    #         customer = Customer.objects.get(customer_id=customer_id, business=default_business)
    #     except Customer.DoesNotExist:
    #         ErrorHandler.validation_error(
    #             message="Customer not found or doesn't belong to this business.",
    #             field="customer_id",
    #             error_code="INVALID_CUSTOMER",
    #             extra_data={
    #                 "customer_id": customer_id,
    #                 "business_id": default_business,
    #             }
    #         )

    #     # Create order
    #     order = Order.objects.create(
    #         customer=customer,
    #         business=default_business,
    #         **validated_data,
    #     )

    #     # Create order products
    #     for product_data in order_products_data:
    #         product_id = product_data.get("product_id")
    #         quantity = product_data.get("quantity")
    #         price = product_data.get("price")
    #         meta = product_data.get("meta", {})

    #         # Validate product belongs to business
    #         try:
    #             product = Product.objects.get(id=product_id, business=default_business)
    #         except Product.DoesNotExist:
    #             ErrorHandler.validation_error(
    #                 message="Product not found or doesn't belong to this business.",
    #                 field="product_id",
    #                 error_code="INVALID_PRODUCT",
    #                 extra_data={"product_id": product_id, "business_id": default_business.id}
    #             )

    #         # Convert price to decimal
    #         try:
    #             price_value = Decimal(str(price))
    #             price_value = price_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    #         except (TypeError, ValueError, InvalidOperation) as e:
    #             ErrorHandler.validation_error(
    #                 message=f"Invalid price format: {str(e)}",
    #                 field="price",
    #                 error_code="INVALID_PRICE_FORMAT",
    #                 extra_data={"price_data": price}
    #             )

    #         OrderProduct.objects.create(
    #             order=order,
    #             product=product,
    #             quantity=quantity,
    #             price=price_value,
    #             meta=meta
    #         )

    #     # Aggregate order totals
    #     order.aggregate()

    #     return order

    # def update(self, instance, validated_data):
    #     request = self.context.get("request")
    #     user = request.user
    #     default_business = user.get_default_business()

    #     # Extract nested data
    #     order_products_data = validated_data.pop(
    #         "order_products_data",
    #         None,
    #     )
    #     customer_id = validated_data.pop("customer_id", None)

    #     # Update customer if provided
    #     if customer_id:
    #         try:
    #             customer = Customer.objects.get(
    #                 customer_id=customer_id,
    #                 business=default_business,
    #             )
    #             instance.customer = customer
    #         except Customer.DoesNotExist:
    #             ErrorHandler.validation_error(
    #                 message="Customer not found or doesn't belong to this business.",
    #                 field="customer_id",
    #                 error_code="INVALID_CUSTOMER",
    #                 extra_data={"customer_id": customer_id, "business_id": default_business}
    #             )

    #     # Update order fields
    #     for attr, value in validated_data.items():
    #         setattr(instance, attr, value)

    #     instance.save()

    #     # Update order products if provided
    #     if order_products_data is not None:
    #         # Clear existing order products
    #         instance.order_products.all().delete()

    #         # Create new order products
    #         for product_data in order_products_data:
    #             product_id = product_data.get("product_id")
    #             quantity = product_data.get("quantity")
    #             price = product_data.get("price")
    #             meta = product_data.get("meta", {})

    #             # Validate product belongs to business
    #             try:
    #                 product = Product.objects.get(id=product_id, business=default_business)
    #             except Product.DoesNotExist:
    #                 ErrorHandler.validation_error(
    #                     message="Product not found or doesn't belong to this business.",
    #                     field="product_id",
    #                     error_code="INVALID_PRODUCT",
    #                     extra_data={"product_id": product_id, "business_id": default_business.id}
    #                 )

    #             # Convert price to decimal
    #             try:
    #                 price_value = Decimal(str(price))
    #                 price_value = price_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    #             except (TypeError, ValueError, InvalidOperation) as e:
    #                 ErrorHandler.validation_error(
    #                     message=f"Invalid price format: {str(e)}",
    #                     field="price",
    #                     error_code="INVALID_PRICE_FORMAT",
    #                     extra_data={"price_data": price}
    #                 )

    #             OrderProduct.objects.create(
    #                 order=instance,
    #                 product=product,
    #                 quantity=quantity,
    #                 price=price_value,
    #                 meta=meta
    #             )

    #         # Re-aggregate order totals
    #         instance.aggregate()

    #     return instance
