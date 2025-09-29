import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests.exceptions import HTTPError
from django.conf import settings


class VapiError(Exception):
    """Custom error for Vapi upstream issues."""


class VapiClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or settings.VAPI_API_KEY
        self.base_url = (base_url or settings.VAPI_BASE_URL).rstrip("/")
        if not self.api_key:
            raise VapiError("VAPI_API_KEY is not configured")

        # --- timeouts (configurable) ---
        self.connect_timeout = int(getattr(settings, "VAPI_CONNECT_TIMEOUT", 10))
        self.read_timeout = int(getattr(settings, "VAPI_READ_TIMEOUT", 300))  # up to 5 minutes

        # --- paths (configurable) ---
        # কিছু ইমপ্লিমেন্টেশনে /chat-এই স্ট্রিম করে; না হলে /chat/stream ব্যবহার করুন
        self.chat_stream_path = getattr(settings, "VAPI_CHAT_STREAM_PATH", "/chat/stream")

        # --- session with retries ---
        self.session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.8,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"],
            raise_on_status=False,  # we'll call raise_for_status ourselves
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    # ---------- Helpers ----------
    def _post_json(self, url: str, payload: dict, *, stream: bool = False) -> requests.Response:
        try:
            r = self.session.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=(self.connect_timeout, self.read_timeout),
                stream=stream,
            )
            # If HTTP error, raise for status to surface quickly
            r.raise_for_status()
            return r
        except HTTPError as e:
            # Attach upstream body for easier debugging
            body = getattr(e.response, "text", "")
            raise VapiError(f"Vapi HTTP {e.response.status_code}: {body}") from e
        except requests.exceptions.ReadTimeout as e:
            raise VapiError("Vapi ReadTimeout: upstream took too long to respond") from e
        except requests.exceptions.RequestException as e:
            raise VapiError(f"Vapi request error: {e}") from e

    # ---------- Public API ----------
    def create_assistant(
        self,
        *,
        name: str | None,
        first_message: str,
        system_prompt: str,
        model_provider: str,
        model_name: str,
    ) -> dict:
        url = f"{self.base_url}/assistant"
        payload = {
            "name": name or "",
            "firstMessage": first_message,
            "firstMessageMode": "assistant-speaks-first",
            "model": {
                "provider": model_provider,
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt}
                ],
            },
        }
        r = self._post_json(url, payload, stream=False)
        return r.json()

    def create_chat(self, *, assistant_id: str, input_text: str) -> dict:
        url = f"{self.base_url}/chat"
        payload = {"assistantId": assistant_id, "input": input_text}
        r = self._post_json(url, payload, stream=False)
        return r.json()

    def create_chat_stream(self, *, assistant_id: str, input_text: str):
        """
        Server-Sent Events (SSE) / chunked stream reader.
        NOTE: If your Vapi workspace streams from /chat directly, set:
              VAPI_CHAT_STREAM_PATH=/chat  in settings/env.
        """
        path = self.chat_stream_path if self.chat_stream_path.startswith("/") else f"/{self.chat_stream_path}"
        url = f"{self.base_url}{path}"
        payload = {"assistantId": assistant_id, "input": input_text}

        # Prefer SSE; Accept header helps some gateways
        stream_headers = {**self.headers, "Accept": "text/event-stream"}
        try:
            r = self.session.post(
                url,
                json=payload,
                headers=stream_headers,
                timeout=(self.connect_timeout, self.read_timeout),
                stream=True,
            )
            r.raise_for_status()
        except HTTPError as e:
            body = getattr(e.response, "text", "")
            raise VapiError(f"Vapi HTTP {e.response.status_code}: {body}") from e
        except requests.exceptions.ReadTimeout as e:
            raise VapiError("Vapi ReadTimeout: upstream took too long to start/continue stream") from e
        except requests.exceptions.RequestException as e:
            raise VapiError(f"Vapi request error: {e}") from e

        # iter_lines keeps stream alive; decode unicode chunks
        return r.iter_lines(decode_unicode=True)

    @staticmethod
    def extract_answer(chat_json: dict) -> str | None:
        """
        Try to pick a concise assistant message from non-streaming chat response.
        """
        if not isinstance(chat_json, dict):
            return None
        outputs = chat_json.get("output") or chat_json.get("messages") or []
        if isinstance(outputs, list):
            for item in outputs:
                if isinstance(item, dict) and item.get("role") in ("assistant", "model"):
                    return item.get("content")
        return None
