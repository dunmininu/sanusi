from rest_framework import serializers
from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "business",
            "message_id",
            "message_content",
            "sanusi_response",
            "sender_email",
            "chat_session",
            "channel",
            "conversation_id",
        ]


class AllMessagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "id",
            "message_id",
            "message_content",
            "sanusi_response",
            "sender_email",
            "channel",
        ]


class MessageInputSerializer(serializers.Serializer):
    message_id = serializers.CharField(required=True)
    message = serializers.CharField(required=True)
    channel = serializers.CharField(required=True)
    # name = serializers.CharField(required=False, allow_null=True)
    knowledge_base = serializers.CharField(required=False, allow_null=True)
    business_id = serializers.IntegerField(required=False, allow_null=True)
    knowledge_id = serializers.IntegerField(required=False, allow_null=True)
    instructions = serializers.CharField(required=False, allow_null=True)
