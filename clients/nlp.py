import logging
import re
import time
from threading import Lock
from typing import ClassVar

import spacy

logger = logging.getLogger(__name__)

SPACY_MODEL_NAME = "es_core_news_sm"
# AnCora entity labels used by the Spanish spaCy pipeline.
ENTITY_LABELS = ("MISC", "ORG", "PER", "LOC")
MIN_TOPIC_LENGTH = 3
# Small models label interrogatives and filler words as entities; those are
# noise, not topics.
NOISE_WORDS: ClassVar[set[str]] = {
    "qué",
    "que",
    "sí",
    "si",
    "vale",
    "bueno",
    "nada",
    "hola",
    "gracias",
    "ok",
    "cuál",
    "cual",
    "cómo",
    "como",
    "dónde",
    "donde",
    "cuándo",
    "cuando",
}
MAX_CANDIDATES = 10
MAX_CANDIDATE_LENGTH = 200

QUOTED_TEXT_PATTERN = re.compile(r"[«“\"']([^«»“”\"']{3,})[»”\"']")


class SpacyTopicExtractor:
    """Picks the concrete topic worth googling using spaCy NER.

    Fully offline, deterministic and key-free. Extraction order: named
    entities found by the model, then text between quotes, then runs of
    mid-sentence capitalized words; ``None`` when nothing specific enough
    shows up so the reaction can fall back to the full text. The model is
    loaded lazily so bot startup is not slowed down.
    """

    def __init__(self, model_name: str = SPACY_MODEL_NAME) -> None:
        self._model_name = model_name
        self._model = None
        self._lock = Lock()
        self._loading = False

    @property
    def is_ready(self) -> bool:
        return self._model is not None

    def ensure_loaded(self) -> None:
        """Load the model without blocking extraction.

        Idempotent and never raises: callers that warm the model up in the
        background (or mid-extraction) just get a warning when it fails.
        """
        if self._model is not None or self._loading:
            return
        self._loading = True
        try:
            self._ensure_model()
        except Exception as error:  # noqa: BLE001 - failures degrade to None
            logger.warning("spaCy model load failed: %s", error)
        finally:
            self._loading = False

    def extract_topic(
        self,
        message: str | None,
        reply_text: str | None = None,
        history: list[str] | tuple[str, ...] = (),
    ) -> str | None:
        """The topic to google for a message someone got lost with.

        Never raises: any model failure logs a warning and degrades to
        ``None`` so the caller can fall back to plain behaviour.
        """
        candidates = self._candidates(message, reply_text, history)
        if not candidates:
            return None
        try:
            model = self._ensure_model()
        except Exception as error:  # noqa: BLE001 - failures degrade to None
            logger.warning("spaCy model load failed: %s", error)
            return None
        docs = list(model.pipe(candidates[:MAX_CANDIDATES]))
        for text, doc in zip(candidates, docs):
            for entity in doc.ents:
                if (
                    entity.label_ not in ENTITY_LABELS
                    or len(entity.text) < MIN_TOPIC_LENGTH
                ):
                    continue
                cleaned = entity.text.strip("¿?¡!.,;:").lower()
                if all(word in NOISE_WORDS for word in cleaned.split()):
                    continue
                # Small models split multi-word proper nouns; when the
                # capitalized run of the same text contains the entity, the
                # full run is the better query.
                extended = self._capitalized_topic(text)
                if (
                    extended
                    and len(extended) > len(entity.text)
                    and entity.text.lower() in extended.lower()
                ):
                    return extended
                return entity.text
        for text in candidates:
            quoted = self._quoted_topic(text)
            if quoted:
                return quoted
        for text in candidates:
            capitalized = self._capitalized_topic(text)
            if capitalized:
                return capitalized
        # The trigger message is mostly filler ("no sé de qué me hablas");
        # only reply-to and history texts are worth mining for nouns.
        noun_docs = docs[: len(docs) - 1] if message else docs
        for doc in noun_docs:
            nouns = self._noun_topic(doc)
            if nouns:
                return nouns
        return None

    # --- layers --------------------------------------------------------------

    @staticmethod
    def _noun_topic(doc) -> str | None:
        """Longest non-noise noun of the text, for lowercase topics like
        "me flipa internet" that no other layer can isolate."""
        nouns = [
            token.text
            for token in doc
            if token.pos_ in ("NOUN", "PROPN")
            and not token.is_stop
            and token.lemma_.lower() not in NOISE_WORDS
            and len(token.text) >= MIN_TOPIC_LENGTH
        ]
        return max(nouns, key=len) if nouns else None

    @staticmethod
    def _quoted_topic(text: str) -> str | None:
        match = QUOTED_TEXT_PATTERN.search(text)
        return match.group(1).strip() if match else None

    @staticmethod
    def _capitalized_topic(text: str) -> str | None:
        tokens = text.split()
        glue = {"de", "del", "la", "el", "los", "las", "y", "e"}
        best_run: list[str] = []
        run: list[str] = []
        glue_streak = 0
        for index, token in enumerate(tokens):
            if index > 0 and token[0].isupper():
                run.append(token)
                glue_streak = 0
            elif run and token.lower() in glue and glue_streak < 2:
                run.append(token)
                glue_streak += 1
            else:
                if len(run) > len(best_run):
                    best_run = run
                run = []
                glue_streak = 0
        if len(run) > len(best_run):
            best_run = run
        while best_run and best_run[-1].lower() in glue:
            best_run.pop()
        return " ".join(best_run) if best_run else None

    # --- plumbing ------------------------------------------------------------

    def _candidates(
        self,
        message: str | None,
        reply_text: str | None,
        history: list[str] | tuple[str, ...],
    ) -> list[str]:
        candidates = []
        if reply_text:
            candidates.append(reply_text)
        candidates.extend(list(history)[::-1])
        if message:
            candidates.append(message)
        return [text[:MAX_CANDIDATE_LENGTH] for text in candidates if text]

    def _ensure_model(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    started = time.monotonic()
                    logger.info("Loading spaCy model %s", self._model_name)
                    self._model = spacy.load(self._model_name)
                    logger.info(
                        "spaCy model %s ready in %.1fs",
                        self._model_name,
                        time.monotonic() - started,
                    )
        return self._model


topic_extractor = SpacyTopicExtractor()
