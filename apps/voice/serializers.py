from rest_framework import serializers
from .models import Conversation, Utterance

class UtteranceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utterance
        fields = ["id","role","text","audio","duration_ms","created_at"]

class ConversationSerializer(serializers.ModelSerializer):
    utterances = UtteranceSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = [
            "id","created_at","updated_at","session_label",
            "name","phone","address","postal_code","city",
            "customer_type","bedrooms","pest_type","notes",
            "booking_time","escalated","utterances"
        ]
