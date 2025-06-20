from django.urls import path
from rest_framework import routers

from .views import ChatViewSet, CustomerViewSet


app_name = "chat"

router = routers.DefaultRouter()
router.register("chat", ChatViewSet, basename="chat")
router.register(
    r"business/(?P<company_id>[^/]+)/customers", CustomerViewSet, basename="customer"
)

# urlpatterns = [
#     # Your other URL patterns...
#     path("create-chat", views.create_chat, name="create_chat"),
#     path("end/<int:chat_id>/", views.end_chat, name="end_chat"),
#     path("send-message/<int:chat_id>/", views.send_message_view, name="send_message"),
#     path("get_messages/<int:chat_id>/", views.get_messages, name="get_messages"),
#     path(
#         "get_active_chats/",
#         views.get_active_chats,
#         name="get_active_chats",
#     ),
#     path(
#         "toggle-chat-status/<int:chat_id>/",
#         views.toggle_chat_status,
#         name="toggle_chat_status",
#     ),
#     path(
#         "bulk-toggle-chat-status/",
#         views.bulk_toggle_status,
#         name="bulk_toggle_chat_status",
#     ),
#     path("chat/", views.ChatViewSet, name="chat"),
# ]
