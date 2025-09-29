from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import StreamingHttpResponse

from .serializers import (
    AssistantCreateSerializer,
    AssistantResponseSerializer,
    ChatCreateSerializer,
)
from .models import Assistant
from .services.vapi import VapiClient, VapiError


class AssistantCreateView(APIView):
    def post(self, request):
        s = AssistantCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data

        client = VapiClient()
        try:
            v = client.create_assistant(
                name=data.get("name"),
                first_message=data["first_message"],
                system_prompt=data["system_prompt"],
                model_provider=data.get("model_provider", "anthropic"),
                model_name=data.get("model_name", "claude-3-sonnet-20240229"),
            )
        except VapiError as e:
            return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        assistant = Assistant.objects.create(
            name=data.get("name", ""),
            vapi_assistant_id=v.get("id"),
            first_message=data["first_message"],
            system_prompt=data["system_prompt"],
            model_provider=data.get("model_provider", "anthropic"),
            model_name=data.get("model_name", "claude-3-sonnet-20240229"),
        )

        out = AssistantResponseSerializer({
            "id": assistant.id,
            "vapi_assistant_id": assistant.vapi_assistant_id,
            "name": assistant.name,
        }).data
        return Response(out, status=status.HTTP_201_CREATED)


class ChatCreateView(APIView):
    """
    Non-streaming chat: waits for full response.
    Use this if you want a single JSON after the model finishes.
    """
    def post(self, request):
        s = ChatCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data

        client = VapiClient()
        try:
            chat = client.create_chat(
                assistant_id=data["assistant_id"],
                input_text=data["input"],
            )
        except VapiError as e:
            # Upstream slow or error → return 504/502 accordingly
            msg = str(e)
            status_code = status.HTTP_504_GATEWAY_TIMEOUT if "ReadTimeout" in msg else status.HTTP_502_BAD_GATEWAY
            return Response({"detail": msg}, status=status_code)

        answer = VapiClient.extract_answer(chat)
        return Response({"assistant_answer": answer, "raw": chat}, status=status.HTTP_200_OK)


class ChatStreamView(APIView):
    """
    Streaming chat via Server-Sent Events (SSE).
    This returns chunks as they arrive; great for long generations.
    """
    def post(self, request):
        s = ChatCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data

        client = VapiClient()
        try:
            lines = client.create_chat_stream(
                assistant_id=data["assistant_id"],
                input_text=data["input"],
            )
        except VapiError as e:
            msg = str(e)
            status_code = status.HTTP_504_GATEWAY_TIMEOUT if "ReadTimeout" in msg else status.HTTP_502_BAD_GATEWAY
            return Response({"detail": msg}, status=status_code)

        def event_stream():
            # If upstream sends SSE, lines typically look like: "data: {...}"
            try:
                for line in lines:
                    if not line:
                        continue
                    # Pass through as raw line per SSE (client can parse)
                    yield line + "\n"
            except Exception:
                # end stream gracefully on any error
                yield "event: error\ndata: stream_ended\n\n"

        return StreamingHttpResponse(event_stream(), content_type="text/event-stream")
