from rest_framework import serializers

class AssistantCreateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True)
    first_message = serializers.CharField()
    system_prompt = serializers.CharField()
    model_provider = serializers.CharField(required=False, default="anthropic")
    model_name = serializers.CharField(required=False, default="claude-3-sonnet-20240229")

class AssistantResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    vapi_assistant_id = serializers.CharField()
    name = serializers.CharField(allow_blank=True)

class ChatCreateSerializer(serializers.Serializer):
    assistant_id = serializers.CharField(help_text="Vapi assistant id")
    input = serializers.CharField()
