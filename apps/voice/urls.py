from django.urls import path
from rest_framework.routers import DefaultRouter
from django.views.generic import TemplateView
from .views import ConversationViewSet, StartConversation

router = DefaultRouter()
router.register(r"conversations", ConversationViewSet, basename="conversation")

urlpatterns = [
    path("", TemplateView.as_view(template_name="widget.html"), name="widget"),  # http://127.0.0.1:8000/
    path("start/", StartConversation.as_view(), name="start-conversation"),
]
urlpatterns += router.urls
