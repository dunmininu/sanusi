from django.db.models import Count
from chat.models import SENDER_CHOICES, Chat, ChatStatus, Customer, Message


def total_customers_per_business(business):
    customers = Customer.objects.filter(customer_chats__business=business).distinct()
    return customers


def get_unique_customer_count():
    unique_customers = Customer.objects.annotate(
        chat_count=Count("customer_chats")
    ).filter(chat_count__gt=0)
    return unique_customers.count()


def get_total_customer_messages():
    total_messages = Message.objects.filter(sender=SENDER_CHOICES.CUSTOMER).count()
    return total_messages


def get_customer_satisfaction():
    positive_messages = Chat.objects.filter(sentiment="positive").count()
    neutral_messages = Chat.objects.filter(sentiment="neutral").count()
    negative_messages = Chat.objects.filter(sentiment="negative").count()

    total_messages = positive_messages + neutral_messages + negative_messages
    satisfaction = (
        (positive_messages / total_messages) * 100 if total_messages > 0 else 0
    )

    return {
        "positive": positive_messages,
        "neutral": neutral_messages,
        "negative": negative_messages,
        "satisfaction_percentage": satisfaction,
    }


def get_escalation_percentage():
    total_messages = Message.objects.count()
    escalted_chats = Chat.objects.filter(escalated=True).count()

    escalation_percentage = (
        (escalted_chats / total_messages) * 100 if total_messages > 0 else 0
    )
    return escalation_percentage


def get_abandonment_percentage():
    total_interactions = Chat.objects.count()
    abandoned_interactions = Chat.objects.filter(
        status=ChatStatus.ACTIVE, end_time__isnull=True
    ).count()

    abandonment_percentage = (
        (abandoned_interactions / total_interactions) * 100
        if total_interactions > 0
        else 0
    )
    return abandonment_percentage


def get_repeat_interaction_counts():
    repeat_interactions = (
        Chat.objects.values("customer")
        .annotate(
            repeat_count=Count("customer"),
        )
        .filter(repeat_count__gt=1)
    )

    return repeat_interactions


def get_sentiment_distribution():
    sentiment_counts = Chat.objects.values("sentiment").annotate(
        sentiment_count=Count("sentiment")
    )

    total_messages = Message.objects.count()
    sentiment_distribution = {
        sentiment["sentiment"]: (sentiment["sentiment_count"] / total_messages) * 100
        for sentiment in sentiment_counts
    }

    return sentiment_distribution
