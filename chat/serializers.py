from rest_framework import serializers
from .models import Chat, Customer, Message
from business.models import Business
from sanusi_backend.utils.error_handler import ErrorHandler


class CreateChatRequestSerializer(serializers.Serializer):
    name = serializers.CharField()
    customer_email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False)


class CustomerSerializer(serializers.ModelSerializer):
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
            "date_created",
        ]
        read_only_fields = [
            "id",
            "identifier",
            "business",
            "date_created",
        ]  # Prevent user from manually setting it
   
    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        company_id = self.context["view"].kwargs.get("company_id")
        if not company_id or not Business.objects.filter(id=company_id).exists():
            ErrorHandler.validation_error(
                message="Valid Company ID required",
                field="company_id",
                error_code="INVALID_COMPANY_ID",
                extra_data={"provided_id": company_id},
            )

        try:
            business = user.businesses.get(id=company_id)
        except Business.DoesNotExist:
            ErrorHandler.validation_error(
                message="Invalid business for current user.",
                field="company_id",
                error_code="INVALID_COMPANY_ID",
                extra_data={"provided_id": company_id},
            )
        customer = Customer(**validated_data)
        customer.business = business
        customer.identifier = customer.generate_identifier()
        customer.save()
        return customer

    def update(self, instance, validated_data):
        request = self.context.get("request")
        user = request.user
        company_id = self.context["view"].kwargs.get("company_id")
        if not company_id or not Business.objects.filter(id=company_id).exists():
            ErrorHandler.validation_error(
                message="Valid Company ID required",
                field="company_id",
                error_code="INVALID_COMPANY_ID",
                extra_data={"provided_id": company_id},
            )
        try:
            business = user.businesses.get(id=company_id)
            company_id == business.id
        except Business.DoesNotExist:
            ErrorHandler.validation_error(
                message="Invalid business for current user.",
                field="company_id",
                error_code="INVALID_COMPANY_ID",
                extra_data={"provided_id": company_id},
            )
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "id",
            "sender",
            "content",
            "sent_time",
            "sanusi_response",
        ]


class ChatListDetailSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)

    class Meta:
        model = Chat
        fields = [
            "identifier",
            "status",
            "customer",
            "channel",
            "sentiment",
            "escalated",
            "keyword",
            "department",
            "start_time",
            "end_time",
        ]


class ChatSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Chat
        fields = [
            "id",
            "customer",
            "status",
            "read",
            "start_time",
            "sentiment",
            "identifier",
            "end_time",
            "messages",
        ]


class AutoResponseSerializer(serializers.Serializer):
    message = serializers.CharField(required=False, allow_null=True)
    sender = serializers.CharField(required=False, allow_null=True)
    channel = serializers.CharField(required=False, allow_null=True)
    customer_name = serializers.CharField(required=False, allow_null=True)
    customer_identifier = serializers.CharField(required=False, allow_null=True)
    customer_email = serializers.CharField(required=False, allow_null=True)


class RestructureTextSerializer(serializers.Serializer):
    channel = serializers.CharField()
    content = serializers.CharField()


class IdsSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.CharField())
