"""Provider tests using a scripted fake Groq client (no SDK, no network)."""

import asyncio
from types import SimpleNamespace

import pytest

from app.providers.base import (
    GenerationRequest,
    ProviderAuthError,
    ProviderBadRequest,
    ProviderEmptyResponse,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnavailable,
)
from app.providers.groq_provider import GroqProvider, translate_exception
from app.providers.mock_provider import MockProvider


class APITimeoutError(Exception):
    pass


class APIConnectionError(Exception):
    pass


class StatusError(Exception):
    def __init__(self, status, headers=None):
        super().__init__(f"HTTP {status}")
        self.status_code = status
        self.response = SimpleNamespace(headers=headers or {})


def completion(text, finish="stop"):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text), finish_reason=finish)],
        usage=SimpleNamespace(prompt_tokens=11, completion_tokens=7),
    )


def chunk(text=None, finish=None):
    return SimpleNamespace(
        choices=[SimpleNamespace(delta=SimpleNamespace(content=text), finish_reason=finish)], usage=None, x_groq=None
    )


async def agen(items):
    for item in items:
        yield item


class FakeClient:
    def __init__(self, script):
        self.script = list(script)
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))
        self.models = SimpleNamespace(list=self._list)

    async def _create(self, **kwargs):
        self.calls.append(kwargs)
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    async def _list(self):
        return SimpleNamespace(data=[SimpleNamespace(id="openai/gpt-oss-120b")])


def make(script, **kw):
    client = FakeClient(script)
    return GroqProvider(client=client, model="openai/gpt-oss-120b", fallback_model="openai/gpt-oss-20b", **kw), client


REQ = GenerationRequest(messages=[{"role": "system", "content": "s"}, {"role": "user", "content": "hi"}],
                        max_tokens=1000, reasoning_effort="high", max_tokens_ceiling=4000)


def run(coro):
    return asyncio.run(coro)


def test_generate_sends_reasoning_params_for_gpt_oss_only():
    provider, client = make([completion("hello world")])
    result = run(provider.generate(REQ))
    assert result.text == "hello world" and result.prompt_tokens == 11 and result.completion_tokens == 7
    assert client.calls[0]["extra_body"] == {"reasoning_effort": "high", "include_reasoning": False}
    assert client.calls[0]["max_completion_tokens"] == 1000

    provider, client = make([completion("hi there")])
    run(provider.generate(GenerationRequest(messages=REQ.messages, model="llama-3.3-70b-versatile",
                                            reasoning_effort="high")))
    assert "extra_body" not in client.calls[0]


def test_rejected_reasoning_params_are_retried_without_them():
    provider, client = make([StatusError(400), completion("fine")])
    assert run(provider.generate(REQ)).text == "fine"
    assert "extra_body" in client.calls[0] and "extra_body" not in client.calls[1]


def test_rate_limit_falls_back_to_secondary_model():
    provider, client = make([StatusError(429, {"retry-after": "3"}), completion("from fallback")])
    result = run(provider.generate(REQ))
    assert result.used_fallback and result.model == "openai/gpt-oss-20b"
    assert client.calls[1]["model"] == "openai/gpt-oss-20b"


def test_auth_error_does_not_fall_back():
    provider, client = make([StatusError(401)])
    with pytest.raises(ProviderAuthError):
        run(provider.generate(REQ))
    assert len(client.calls) == 1


def test_both_models_failing_raises_last_error_with_retry_after():
    provider, _ = make([StatusError(429), StatusError(429, {"retry-after": "9"})])
    with pytest.raises(ProviderRateLimited) as info:
        run(provider.generate(REQ))
    assert info.value.retry_after == 9 and info.value.status_code == 429


def test_reasoning_that_eats_the_budget_is_retried_with_more_room():
    provider, client = make([completion("", "length"), completion("answer now")])
    result = run(provider.generate(REQ))
    assert result.text == "answer now"
    assert client.calls[1]["max_completion_tokens"] == 2000
    assert client.calls[1]["extra_body"]["reasoning_effort"] == "low"


def test_empty_response_is_an_error():
    provider, _ = make([completion("   ", "stop")])
    with pytest.raises(ProviderEmptyResponse):
        run(provider.generate(REQ))


def test_streaming_yields_deltas_then_final():
    provider, _ = make([agen([chunk("Hel"), chunk("lo"), chunk(None, "stop")])])

    async def collect():
        return [event async for event in provider.stream(REQ)]

    events = run(collect())
    assert [e.text for e in events if e.kind == "delta"] == ["Hel", "lo"]
    assert events[-1].kind == "final" and events[-1].result.text == "Hello"
    assert events[-1].result.finish_reason == "stop"


def test_streaming_falls_back_before_first_token():
    provider, client = make([StatusError(503), agen([chunk("ok"), chunk(None, "stop")])])

    async def collect():
        return [event async for event in provider.stream(REQ)]

    events = run(collect())
    assert events[-1].result.used_fallback and client.calls[1]["model"] == "openai/gpt-oss-20b"


def test_healthcheck_reports_model_availability():
    provider, _ = make([])
    info = run(provider.healthcheck())
    assert info["reachable"] and info["model_available"] and info["fallback_available"] is False


def test_translate_exception_mapping():
    assert isinstance(translate_exception(APITimeoutError("t")), ProviderTimeout)
    assert isinstance(translate_exception(APIConnectionError("c")), ProviderUnavailable)
    assert isinstance(translate_exception(StatusError(400)), ProviderBadRequest)
    assert isinstance(translate_exception(StatusError(502)), ProviderUnavailable)
    error = translate_exception(StatusError(429, {"retry-after": "2"}))
    assert error.retry_after == 2


def test_error_messages_never_contain_keys():
    error = translate_exception(StatusError(400))
    leaky = Exception("bad key gsk_" + "Z9" * 20)
    leaky.status_code = 400
    assert "gsk_" not in translate_exception(leaky).message and error.message


def test_mock_provider_is_deterministic_and_streams():
    provider = MockProvider()
    first = run(provider.generate(REQ)).text
    assert first == run(provider.generate(REQ)).text and "strategy=" in first

    async def collect():
        return "".join([e.text async for e in provider.stream(REQ) if e.kind == "delta"])

    assert run(collect()) == first
