from django.contrib import admin
from .models import Conversation, Utterance

admin.site.register(Conversation)
admin.site.register(Utterance)