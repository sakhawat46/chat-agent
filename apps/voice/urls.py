# assistants/urls.py
from django.urls import path
from .views import AssistantCreateView, ChatCreateView, ChatStreamView

urlpatterns = [
    path("assistants/", AssistantCreateView.as_view(), name="assistant-create"),
    path("chats/", ChatCreateView.as_view(), name="chat-create"),
    path("chats/stream/", ChatStreamView.as_view(), name="chat-stream"),
]
