import json

import httpx
import pytest

from clients.llm import LlmClient


def completion_response(content):
    return {"choices": [{"message": {"content": content}}]}


def make_client(handler):
    return LlmClient(transport=httpx.MockTransport(handler))


@pytest.fixture
def configured_env(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://llm.test/v1")
    monkeypatch.setenv("LLM_MODEL", "test-model")


def test_client_needs_an_api_key_to_be_configured(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    assert LlmClient().is_configured is False

    monkeypatch.setenv("LLM_API_KEY", "key")
    assert LlmClient().is_configured is True


@pytest.mark.asyncio
async def test_extract_posts_an_openai_compatible_request(configured_env):
    captured = {}

    def handler(request):
        captured["method"] = request.method
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        captured["json"] = json.loads(request.content)
        return httpx.Response(
            200, json=completion_response('{"query": "Angine de Poitrine"}')
        )

    client = make_client(handler)
    query = await client.extract_search_query(
        "no sé de qué habláis",
        reply_text="Qué buena banda es Angine de Poitrine",
        history=["Sí, me encantan"],
    )

    assert query == "Angine de Poitrine"
    assert captured["method"] == "POST"
    assert captured["url"] == "https://llm.test/v1/chat/completions"
    assert captured["headers"]["authorization"] == "Bearer test-key"
    assert captured["json"]["model"] == "test-model"
    assert captured["json"]["temperature"] == 0
    assert [message["role"] for message in captured["json"]["messages"]] == [
        "system",
        "user",
    ]
    user_prompt = json.loads(captured["json"]["messages"][1]["content"])
    assert user_prompt["replied_to"] == "Qué buena banda es Angine de Poitrine"
    assert user_prompt["previous_messages"] == ["Sí, me encantan"]
    assert user_prompt["message_that_got_lost"] == "no sé de qué habláis"


@pytest.mark.asyncio
async def test_extract_returns_the_plain_text_when_the_answer_is_not_json(
    configured_env,
):
    def handler(_request):
        return httpx.Response(200, json=completion_response("Angine de Poitrine"))

    assert await make_client(handler).extract_search_query("ni idea") == (
        "Angine de Poitrine"
    )


@pytest.mark.asyncio
async def test_extract_strips_quotes_from_the_answer(configured_env):
    def handler(_request):
        return httpx.Response(200, json=completion_response('"Angine de Poitrine"'))

    assert await make_client(handler).extract_search_query("ni idea") == (
        "Angine de Poitrine"
    )


@pytest.mark.asyncio
async def test_extract_returns_none_when_the_model_finds_no_topic(configured_env):
    def handler(_request):
        return httpx.Response(200, json=completion_response('{"query": null}'))

    assert await make_client(handler).extract_search_query("ni idea") is None


@pytest.mark.asyncio
async def test_extract_uses_only_the_last_ten_messages(configured_env):
    captured = {}

    def handler(request):
        captured["json"] = json.loads(request.content)
        return httpx.Response(200, json=completion_response('{"query": "hi"}'))

    history = [f"mensaje {index}" for index in range(12)]
    await make_client(handler).extract_search_query("no sé", history=history)

    user_prompt = json.loads(captured["json"]["messages"][1]["content"])
    assert user_prompt["previous_messages"] == [
        f"mensaje {index}" for index in range(2, 12)
    ]


@pytest.mark.asyncio
async def test_extract_degrades_silently_on_http_errors(configured_env):
    def handler(_request):
        return httpx.Response(500)

    assert await make_client(handler).extract_search_query("no sé") is None


@pytest.mark.asyncio
async def test_extract_degrades_silently_on_malformed_payloads(configured_env):
    def handler(_request):
        return httpx.Response(200, json={"unexpected": "shape"})

    assert await make_client(handler).extract_search_query("no sé") is None


@pytest.mark.asyncio
async def test_extract_does_not_call_the_llm_when_unconfigured(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    def should_not_call(_request):
        raise AssertionError("Unconfigured clients must not reach the network")

    assert await make_client(should_not_call).extract_search_query("no sé") is None
