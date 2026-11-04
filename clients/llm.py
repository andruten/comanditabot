import json
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 8
MAX_TOKENS = 100
MAX_TRANSCRIPT_MESSAGE_LENGTH = 200
MAX_TRANSCRIPT_MESSAGES = 10

SYSTEM_PROMPT = (
    "Eres el asistente de un bot de Telegram para un grupo de amigos. "
    "En la conversación, alguien dice que no sabe o no entiende de qué hablan. "
    "Elige el término más concreto para buscar en Google sobre el tema del que "
    "hablan (nombre de banda, película, persona, tecnología u objeto concreto). "
    'Responde exclusivamente con JSON: {"query": "<término>"} o {"query": null} '
    "si no hay nada tan concreto como para merecer una búsqueda. Sin explicaciones."
)


class LlmClient:
    """Minimal OpenAI-compatible chat client.

    Used to pick the exact topic worth googling on behalf of the "let me
    google that for you" reaction. Any server exposing the
    ``/chat/completions`` API (OpenAI, Gemini via its compatibility layer,
    OpenRouter, Ollama, LM Studio...) works through ``LLM_BASE_URL``.
    """

    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.base_url = os.environ.get(
            "LLM_BASE_URL", "https://api.openai.com/v1"
        ).rstrip("/")
        self.api_key = os.environ.get("LLM_API_KEY")
        self.model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
        self.timeout = REQUEST_TIMEOUT_SECONDS
        self._transport = transport

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def extract_search_query(
        self,
        message: str | None,
        reply_text: str | None = None,
        history: list[str] | tuple[str, ...] = (),
    ) -> str | None:
        """Topic to google for a message someone got lost with.

        Never raises: any network, API or parsing failure logs a warning and
        degrades to ``None`` so the caller can fall back to plain behaviour.
        """
        if not self.is_configured:
            return None
        try:
            content = await self.chat(self._chat_messages(message, reply_text, history))
        except Exception as error:  # noqa: BLE001 - failures degrade to None
            logger.warning("LLM topic resolution failed: %s", error)
            return None
        return self.parse_search_query(content)

    async def chat(self, messages: list[dict[str, Any]]) -> str:
        async with httpx.AsyncClient(
            timeout=self.timeout, transport=self._transport
        ) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0,
                    "max_tokens": MAX_TOKENS,
                },
            )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"] or ""

    def parse_search_query(self, content: str | None) -> str | None:
        text = (content or "").strip()
        if not text:
            return None
        try:
            data = json.loads(text)
        except ValueError:
            return self._normalize_query(text)
        if isinstance(data, str):
            return self._normalize_query(data)
        if isinstance(data, dict):
            return self._normalize_query(str(data.get("query") or ""))
        return None

    # --- prompt building ----------------------------------------------------

    def _chat_messages(
        self,
        message: str | None,
        reply_text: str | None,
        history: list[str] | tuple[str, ...],
    ) -> list[dict[str, Any]]:
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": self._user_prompt(message, reply_text, history),
            },
        ]

    def _user_prompt(
        self,
        message: str | None,
        reply_text: str | None,
        history: list[str] | tuple[str, ...],
    ) -> str:
        payload = {
            "replied_to": self._cap(reply_text or ""),
            "previous_messages": [
                self._cap(text) for text in list(history)[-MAX_TRANSCRIPT_MESSAGES:]
            ],
            "message_that_got_lost": self._cap(message or ""),
        }
        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def _cap(text: str) -> str:
        return text[:MAX_TRANSCRIPT_MESSAGE_LENGTH]

    @staticmethod
    def _normalize_query(query: str) -> str | None:
        query = query.strip().strip("\"'«»“”").strip()
        if not query or query.lower() == "none":
            return None
        return query


llm_client = LlmClient()
