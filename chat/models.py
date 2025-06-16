import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField

# from business.models import Business


class ChatStatus(models.TextChoices):
    ACTIVE = ("active", "all active chats")
    RESOLVED = ("resolved", "all resolved chats")


class ChannelChoices(models.TextChoices):
    EMAIL = ("email", "Email address")
    CHAT = ("chat", "Sanusi Chat Channel")
    FACEBOOK = ("facebook", "Business facebook channel")
    TELEGRAM = ("telegram", "Business Telegram channel")
    TWITTER = ("twitter", "Business Twitter channel")


class Customer(models.Model):
    name = models.CharField(max_length=256)
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    identifier = models.CharField(max_length=256, null=True, blank=True, unique=True)

    def generate_identifier(self):
        name = self.name.replace(" ", "")
        identifier = name + "_" + str(uuid.uuid4().hex[:8])
        self.identifier = identifier
        self.save()

    def __str__(self):
        return self.name


class Chat(models.Model):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="customer_chats",
    )
    agent = models.CharField(max_length=52, null=True, blank=True)
    identifier = models.CharField(
        max_length=72,
        null=True,
        blank=True,
    )
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=ChatStatus.choices,
        default=ChatStatus.ACTIVE,
    )
    channel = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=ChannelChoices.choices,
        default=ChannelChoices.CHAT,
    )
    read = models.BooleanField(default=False)
    is_auto_response = models.BooleanField(default=False)
    sentiment = models.CharField(max_length=52, default="")
    keyword = models.CharField(max_length=256, default="")
    escalated = models.BooleanField(default=False)
    department = models.CharField(max_length=256, default="")
    chat_session = ArrayField(models.CharField(max_length=200), blank=True, null=True)

    def generate_identifier(self):
        name = self.customer.name.replace(" ", "")
        identifier = name + "_" + str(uuid.uuid4().hex[:8])
        self.identifier = identifier
        self.save()


class SENDER_CHOICES(models.TextChoices):
    CUSTOMER = ("customer", "a person that initiates the chat")
    AGENT = ("agent", "a person that reponds to the initiated chat")


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(
        max_length=256,
        choices=SENDER_CHOICES.choices,
        default=SENDER_CHOICES.CUSTOMER,
    )
    sanusi_response = models.TextField(null=True, blank=True)
    content = models.TextField()
    sent_time = models.DateTimeField(auto_now_add=True)
    is_multimedia = models.BooleanField(default=False)
    multimedia_url = models.URLField(blank=True, null=True)
