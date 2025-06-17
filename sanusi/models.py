from django.db import models
from chat.models import Chat
import uuid
from sanusi_backend.classes.base_model import BaseModel


# Create your models here.
class ChannelTypes(models.TextChoices):
    EMAIL = ("email", "Email")
    CHAT = ("chat", "Chat")


class Message(BaseModel):
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name="sanusi_messages",
        null=True,
        blank=True,
    )
    message_id = models.UUIDField(
        default=uuid.uuid4, unique=True, db_index=True, primary_key=True
    )
    message_content = models.TextField()
    sanusi_response = models.TextField(blank=True, null=True)
    sender_email = models.EmailField(max_length=30)
    channel = models.CharField(
        max_length=20, choices=ChannelTypes.choices, default=ChannelTypes.EMAIL
    )
    chat_session = models.JSONField(null=True)

    def __str__(self):
        return self.sender_email
