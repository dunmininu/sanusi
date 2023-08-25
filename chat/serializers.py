from rest_framework import serializers
from .models import Chat, Customer, Message


class CreateChatRequestSerializer(serializers.Serializer):
    name = serializers.CharField()
    customer_email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False)


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "email", "phone_number", "identifier"]


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
