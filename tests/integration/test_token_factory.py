"""Explicit HTTP contract doubles. Live provider evidence is recorded separately."""

import asyncio
import json

import httpx
import pytest
from aegis_inference.client import InferenceUnavailable
from aegis_inference.token_factory import MODEL_ORDER, TokenFactoryClient
from pydantic import SecretStr


def response(model):
    return {
        "model": model,
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": json.dumps(
                        {
                            "assessment": "investigate",
                            "hypotheses": ["sensor_bias"],
                            "evidence_ids": ["residuals"],
                        }
                    )
                },
            }
        ],
        "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
    }


def catalog():
    return {"data": [{"id": model, "context_length": 262144} for model in MODEL_ORDER]}


def test_ordered_fallback_and_fixed_origin_use_reviewed_schema_only():
    async def check():
        calls = []

        def double(request):
            assert request.url.host == "developer.amd.com.cn"
            if request.method == "GET":
                return httpx.Response(200, json=catalog())
            body = json.loads(request.content)
            assert "tools" not in body and body["response_format"] == {"type": "json_object"}
            assert [m["role"] for m in body["messages"]] == ["system", "user"]
            calls.append(body["model"])
            if len(calls) == 1:
                return httpx.Response(503)
            assert body["reasoning_effort"] == "low"
            return httpx.Response(200, json=response("self-dploy/" + body["model"]))

        client = TokenFactoryClient(
            SecretStr("http-contract-test-only"), transport=httpx.MockTransport(double)
        )
        try:
            result = await client.investigate("Observed residuals only")
            assert result.model_id == MODEL_ORDER[1] and calls == list(MODEL_ORDER[:2])
            assert result.served_model_id == "self-dploy/" + MODEL_ORDER[1]
            assert not result.hardware_verified and not result.operational_write_allowed
            assert result.prompt_tokens + result.completion_tokens == 120
        finally:
            await client.close()

    asyncio.run(check())


@pytest.mark.parametrize("status", [401, 403, 429])
def test_shared_auth_or_quota_never_fans_out_to_other_models(status):
    async def check():
        calls = []

        def double(request):
            if request.method == "GET":
                return httpx.Response(200, json=catalog())
            calls.append(request.url.path)
            return httpx.Response(status, headers={"Retry-After": "60"})

        client = TokenFactoryClient(
            SecretStr("http-contract-test-only"), transport=httpx.MockTransport(double)
        )
        try:
            with pytest.raises(InferenceUnavailable, match="auth/quota"):
                await client.investigate("data")
            assert len(calls) == 1
        finally:
            await client.close()

    asyncio.run(check())


@pytest.mark.parametrize(
    "attack",
    [
        "wrong_model",
        "wrong_prefix",
        "tool",
        "command",
        "reference",
        "usage",
        "truncation",
        "encoding",
        "oversized",
    ],
)
def test_untrusted_outputs_are_rejected(attack):
    async def check():
        def double(request):
            if request.method == "GET":
                return httpx.Response(200, json=catalog())
            value = response(MODEL_ORDER[0])
            headers = {}
            if attack == "wrong_model":
                value["model"] = "unreviewed-model"
            if attack == "wrong_prefix":
                value["model"] = "untrusted/" + MODEL_ORDER[0]
            if attack == "tool":
                value["choices"][0]["message"]["tool_calls"] = [{"name": "execute"}]
            if attack == "command":
                value["choices"][0]["message"]["content"] = '{"command":"execute"}'
            if attack == "reference":
                value["choices"][0]["message"]["content"] = (
                    '{"assessment":"investigate","hypotheses":[],"evidence_ids":["forged-source"]}'
                )
            if attack == "usage":
                value["usage"]["total_tokens"] = 1
            if attack == "truncation":
                value["choices"][0]["finish_reason"] = "length"
            if attack == "encoding":
                return httpx.Response(200, headers={"content-encoding": "br"}, content=b"x")
            if attack == "oversized":
                return httpx.Response(200, content=b"x" * 131073)
            return httpx.Response(200, json=value, headers=headers)

        client = TokenFactoryClient(
            SecretStr("http-contract-test-only"),
            models=(MODEL_ORDER[0],),
            transport=httpx.MockTransport(double),
        )
        try:
            with pytest.raises(InferenceUnavailable):
                await client.investigate("data")
        finally:
            await client.close()

    asyncio.run(check())


def test_unreviewed_model_and_oversized_evidence_refuse_before_network():
    with pytest.raises(ValueError):
        TokenFactoryClient(SecretStr("test"), models=("unreviewed",))

    async def check():
        client = TokenFactoryClient(
            SecretStr("test"),
            transport=httpx.MockTransport(
                lambda request: (_ for _ in ()).throw(AssertionError("network reached"))
            ),
        )
        try:
            with pytest.raises(ValueError):
                await client.investigate("x" * 16001)
        finally:
            await client.close()

    asyncio.run(check())


def test_field_diagnostics_never_retain_model_text_and_quota_circuit_persists():
    async def check():
        calls = []

        def double(request):
            calls.append(request.method)
            if request.method == "GET":
                return httpx.Response(200, json=catalog())
            value = response(MODEL_ORDER[0])
            value["choices"][0]["message"]["content"] = '{"command":"SECRET-INJECTION"}'
            return httpx.Response(200, json=value)

        client = TokenFactoryClient(
            SecretStr("test"), models=(MODEL_ORDER[0],), transport=httpx.MockTransport(double)
        )
        try:
            with pytest.raises(InferenceUnavailable):
                await client.investigate("observed data")
            diagnostic = json.dumps(client.diagnostics)
            assert "schema_errors" in diagnostic and "extra_forbidden" in diagnostic
            assert "SECRET-INJECTION" not in diagnostic
        finally:
            await client.close()

        def quota(request):
            calls.append(request.method)
            return httpx.Response(429)

        client = TokenFactoryClient(SecretStr("test"), transport=httpx.MockTransport(quota))
        try:
            with pytest.raises(InferenceUnavailable):
                await client.investigate("data")
            before = len(calls)
            with pytest.raises(InferenceUnavailable, match="circuit"):
                await client.plan("data")
            assert len(calls) == before
        finally:
            await client.close()

    asyncio.run(check())


def test_timeout_routes_to_reviewed_fallback_and_planning_has_no_command_payload():
    async def check():
        calls = []

        def double(request):
            if request.method == "GET":
                return httpx.Response(200, json=catalog())
            body = json.loads(request.content)
            calls.append(body["model"])
            if len(calls) == 1:
                raise httpx.ReadTimeout("contract timeout")
            value = response(body["model"])
            value["choices"][0]["message"]["content"] = json.dumps(
                {"recommendation": "emergency_stop", "evidence_ids": ["candidate_evaluations"]}
            )
            return httpx.Response(200, json=value)

        client = TokenFactoryClient(SecretStr("test"), transport=httpx.MockTransport(double))
        try:
            result = await client.plan('{"candidate_evaluations":{}}')
            assert result.opinion.recommendation == "emergency_stop"
            assert calls == list(MODEL_ORDER[:2])
            assert client.diagnostics[0]["rejection_class"] == "ReadTimeout"
            assert not result.operational_write_allowed
        finally:
            await client.close()

    asyncio.run(check())


def test_reference_to_absent_structured_evidence_is_refused():
    async def check():
        client = TokenFactoryClient(
            SecretStr("test"),
            models=(MODEL_ORDER[0],),
            transport=httpx.MockTransport(
                lambda r: httpx.Response(
                    200, json=catalog() if r.method == "GET" else response(MODEL_ORDER[0])
                )
            ),
        )
        try:
            with pytest.raises(InferenceUnavailable):
                await client.investigate('{"observed":{}}')
            assert client.last_diagnostic["stage"] == "references"
        finally:
            await client.close()

    asyncio.run(check())


@pytest.mark.parametrize("payload", [[], {"choices": []}, {"choices": [None]}])
def test_malformed_envelopes_fail_closed(payload):
    async def check():
        client = TokenFactoryClient(
            SecretStr("test"),
            models=(MODEL_ORDER[0],),
            transport=httpx.MockTransport(
                lambda r: httpx.Response(200, json=catalog() if r.method == "GET" else payload)
            ),
        )
        try:
            with pytest.raises(InferenceUnavailable):
                await client.investigate("data")
        finally:
            await client.close()

    asyncio.run(check())
