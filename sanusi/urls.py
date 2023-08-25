from django.urls import path, include

from .views import (
    SanusiMessageChannelViewSet,
    get_single_chat_session,
    get_messages,
)


urlpatterns = [
    path(
        "jarvis-message/",
        SanusiMessageChannelViewSet.as_view(),
        name="jarvis_message_channel",
    ),
    path(
        "get-one-jarvis-message-session/<str:message_id>/",
        get_single_chat_session,
        name="get_single_chat_session",
    ),
    path("get-messages/", get_messages, name="get_messages"),
]
