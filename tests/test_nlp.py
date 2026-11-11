from typing import ClassVar

from clients.nlp import SPACY_MODEL_NAME, SpacyTopicExtractor, topic_extractor


def test_capitalized_topic_finds_mid_sentence_proper_nouns():
    assert SpacyTopicExtractor._capitalized_topic(
        "Qué buena banda es Angine de Poitrine"
    ) == ("Angine de Poitrine")


def test_capitalized_topic_ignores_the_sentence_start_capital():
    assert SpacyTopicExtractor._capitalized_topic("Me encanta Radiohead") == (
        "Radiohead"
    )


def test_capitalized_topic_ignores_the_lowercased_topic():
    assert SpacyTopicExtractor._capitalized_topic("no sé qué es kubernetes") is None


def test_capitalized_topic_trims_trailing_glue():
    assert SpacyTopicExtractor._capitalized_topic(
        "escucha Angine de Poitrine y más cosas"
    ) == ("Angine de Poitrine")


def test_quoted_topic():
    assert SpacyTopicExtractor._quoted_topic(
        'me gusta "Angine de Poitrine", flipad'
    ) == ("Angine de Poitrine")
    assert SpacyTopicExtractor._quoted_topic("no hay comillas aquí") is None


def test_extract_topic_returns_none_without_candidates():
    assert topic_extractor.extract_topic(None, None, ()) is None
    assert topic_extractor.extract_topic("", "", []) is None


def test_extract_topic_picks_the_entity_with_the_real_model():
    assert topic_extractor.extract_topic(
        "no sé de qué habláis",
        history=["Qué buena banda es Angine de Poitrine", "Sí, me encantan"],
    ) == ("Angine de Poitrine")


def test_extract_topic_prefers_the_reply_text():
    topic = topic_extractor.extract_topic(
        "no sé de qué habláis",
        reply_text="Estoy escuchando mucho a Radiohead",
        history=["Qué buena banda es Angine de Poitrine"],
    )
    assert topic in ("Radiohead", "Angine de Poitrine")


def test_extract_topic_returns_none_when_nothing_specific_shows_up():
    assert (
        topic_extractor.extract_topic(
            "no sé de qué habláis",
            history=["sí", "bueno", "vale"],
        )
        is None
    )


def test_extract_topic_falls_back_to_the_longest_noun():
    assert (
        topic_extractor.extract_topic(
            "no sé de qué me hablas", history=["me flipa internet"]
        )
        == "internet"
    )


def test_module_exposes_a_shared_extractor():
    assert isinstance(topic_extractor, SpacyTopicExtractor)


def test_new_extractors_are_not_ready_until_the_model_is_loaded(monkeypatch):
    loads = []

    class FakeDoc:
        ents: ClassVar[list] = []

        def __iter__(self):
            return iter(())

    class FakeModel:
        def pipe(self, texts):
            return [FakeDoc() for _ in texts]

    class FakeSpacy:
        @staticmethod
        def load(name):
            loads.append(name)
            return FakeModel()

    monkeypatch.setattr("clients.nlp.spacy", FakeSpacy)
    extractor = SpacyTopicExtractor()

    assert extractor.is_ready is False
    extractor.ensure_loaded()
    extractor.ensure_loaded()  # cached, no second load

    assert extractor.is_ready is True
    assert loads == [SPACY_MODEL_NAME]
    assert extractor.extract_topic("no sé", history=[]) is None


def test_loading_failures_degrade_to_not_ready(monkeypatch):
    class FakeSpacy:
        @staticmethod
        def load(name):
            raise RuntimeError("model missing")

    monkeypatch.setattr("clients.nlp.spacy", FakeSpacy)
    extractor = SpacyTopicExtractor()

    extractor.ensure_loaded()

    assert extractor.is_ready is False
    assert extractor.extract_topic("no sé", history=["algo de tema"]) is None
