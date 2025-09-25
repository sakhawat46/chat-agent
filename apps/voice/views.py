from django.utils import timezone
from django.core.files.base import ContentFile
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from .models import Conversation, Utterance
from .serializers import ConversationSerializer, UtteranceSerializer
from apps.voice.services.openai_client import transcribe_audio, chat_completion, synthesize_speech
from apps.voice.services.prompt import INSECTICA_SYSTEM_PROMPT
from apps.voice.services.booking import BookingPolicy



class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all().order_by("-created_at")
    serializer_class = ConversationSerializer
    parser_classes = [MultiPartParser, FormParser]

    @action(detail=True, methods=["post"], url_path="ingest_audio")
    def ingest_audio(self, request, pk=None):
        convo = self.get_object()
        audio_file = request.FILES.get("audio")
        duration_ms = int(request.data.get("duration_ms", 0))
        if not audio_file:
            return Response({"detail": "audio required"}, status=400)

        # 1) ইউজার অডিও সেভ
        user_uttr = Utterance.objects.create(
            conversation=convo, role="user", audio=audio_file, duration_ms=duration_ms
        )

        # 2) STT
        text = transcribe_audio(user_uttr.audio.path)
        user_uttr.text = text
        user_uttr.save()

        # 3) কনটেক্সট বিল্ড
        messages = [{"role": "system", "content": INSECTICA_SYSTEM_PROMPT}]
        for u in convo.utterances.all().order_by("created_at"):
            messages.append({"role": u.role, "content": u.text or ""})

        # 4) অ্যাসিস্ট্যান্ট টেক্সট
        assistant_text = chat_completion(messages)

        # 5) TTS
        audio_bytes = synthesize_speech(assistant_text)
        filename = f"assistant_{timezone.now().timestamp()}.mp3"
        assistant_audio_field = ContentFile(audio_bytes, name=filename)

        asr_uttr = Utterance.objects.create(
            conversation=convo, role="assistant", text=assistant_text, audio=assistant_audio_field
        )

        return Response({
            "assistant_text": assistant_text,
            "assistant_audio_url": asr_uttr.audio.url,
            "utterance": UtteranceSerializer(asr_uttr).data,
        }, status=200)

    @action(detail=True, methods=["get"], url_path="summary")
    def summary(self, request, pk=None):
        convo = self.get_object()
        data = ConversationSerializer(convo).data
        return Response(data)

class StartConversation(APIView):
    def post(self, request):
        label = request.data.get("session_label", "web-embed")
        convo = Conversation.objects.create(session_label=label)
        return Response({"conversation_id": convo.id}, status=201)
