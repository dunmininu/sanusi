from django.urls import path, include

from .views import (
    SanusiMessageChannelViewSet,
    get_single_chat_session,
    get_messages,
)


urlpatterns = [
    path(
        "message/",
        SanusiMessageChannelViewSet.as_view(),
        name="_message_channel",
    ),
    path(
        "get-one-message-session/<str:message_id>/",
        get_single_chat_session,
        name="get_single_chat_session",
    ),
    path("get-messages/", get_messages, name="get_messages"),
]
