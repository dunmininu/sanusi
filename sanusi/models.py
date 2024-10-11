from django.db import models
from chat.models import Chat


# Create your models here.
class ChannelTypes(models.TextChoices):
    EMAIL = ("email", "Email")
    CHAT = ("chat", "Chat")


class Message(models.Model):
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name="sanusi_messages",
        null=True,
        blank=True,
    )
    message_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    message_content = models.TextField()
    sanusi_response = models.TextField(blank=True, null=True)
    sender_email = models.EmailField(max_length=30)
    channel = models.CharField(
        max_length=20, choices=ChannelTypes.choices, default=ChannelTypes.EMAIL
    )
    chat_session = models.JSONField(null=True)

    def __str__(self):
        return self.sender_email
