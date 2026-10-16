"""Actual ES256 WebAuthn proofs. Storage/session doubles are isolated test-only."""

import copy
import hashlib
import json
import time
from types import SimpleNamespace
from uuid import uuid4

import cbor2
import pytest
from aegis_agents.optimizer import canonical
from aegis_api.authorization import USER_HANDLE, AuthorizationService
from aegis_api.capabilities import encode
from aegis_contracts.authorization import ApprovalSession, ApprovalView, CredentialResponse
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from pydantic import SecretStr
from test_capability_authorization import proposal

ORIGIN = "http://localhost:8180"
CHALLENGE = b"test-only-unpredictability-is-not-used-here-32"
ID = b"test-credential-id"
KEY = ec.generate_private_key(ec.SECP256R1())
PUB = KEY.public_key().public_numbers()
COSE = cbor2.dumps(
    {1: 2, 3: -7, -1: 1, -2: PUB.x.to_bytes(32, "big"), -3: PUB.y.to_bytes(32, "big")}
)


def response(
    kind="authentication",
    *,
    origin=ORIGIN,
    rp_id="localhost",
    challenge=CHALLENGE,
    uv=True,
    count=1,
    tamper=False,
    user_handle=USER_HANDLE,
):
    client = canonical(
        {
            "type": "webauthn.create" if kind == "registration" else "webauthn.get",
            "challenge": encode(challenge),
            "origin": origin,
            "crossOrigin": False,
        }
    )
    flags = 1 | (4 if uv else 0) | (64 if kind == "registration" else 0)
    auth = hashlib.sha256(rp_id.encode()).digest() + bytes([flags]) + count.to_bytes(4, "big")
    if kind == "registration":
        auth += b"\0" * 16 + len(ID).to_bytes(2, "big") + ID + COSE
        result = {
            "clientDataJSON": encode(client),
            "attestationObject": encode(
                cbor2.dumps({"fmt": "none", "attStmt": {}, "authData": auth})
            ),
        }
    else:
        signature = KEY.sign(auth + hashlib.sha256(client).digest(), ec.ECDSA(hashes.SHA256()))
        if tamper:
            signature = bytes([signature[0] ^ 1]) + signature[1:]
        result = {
            "clientDataJSON": encode(client),
            "authenticatorData": encode(auth),
            "signature": encode(signature),
            "userHandle": encode(user_handle),
        }
    return CredentialResponse(
        ceremony_id=str(uuid4()),
        credential={
            "id": encode(ID),
            "rawId": encode(ID),
            "type": "public-key",
            "response": result,
            "clientExtensionResults": {},
        },
    )


def service(settings):
    item = AuthorizationService.__new__(AuthorizationService)
    item.config = settings.model_copy(
        update={"signing_seed": SecretStr("isolated-webauthn-signing-seed-" * 3)}
    )
    ceremony = {
        "challenge": encode(CHALLENGE),
        "origin": ORIGIN,
        "rp_id": "localhost",
        "session_id": "test-session",
    }
    item._consume = lambda *args: ceremony
    plan = proposal()
    raw = canonical(plan.model_dump()).decode()
    record = {
        "_id": plan.action_id,
        "action_json": raw,
        "plan_sha256": hashlib.sha256(raw.encode()).hexdigest(),
        "status": "waiting_for_passkey",
    }
    ceremony.update(action_id=plan.action_id, plan_sha256=record["plan_sha256"])
    credential = {"_id": encode(ID), "public_key": encode(COSE), "sign_count": 0}
    inserted = []
    item.client = SimpleNamespace(
        aegis=SimpleNamespace(
            auth_credentials=SimpleNamespace(
                insert_one=lambda value: inserted.append(value),
                find_one=lambda query: credential,
                update_one=lambda query, update: SimpleNamespace(matched_count=1),
            ),
            auth_proposals=SimpleNamespace(
                update_one=lambda query, update: SimpleNamespace(modified_count=1)
            ),
        )
    )
    item.session_view = lambda cookie: ApprovalSession(
        enrolled_credentials=1, expires_at=int(time.time()) + 60, canonical_origin=ORIGIN
    )
    item.proposal = lambda cookie, action_id: record
    item.gateway = SimpleNamespace(check_current=lambda *args: None, resource=lambda: {})
    item.view = lambda cookie, action_id: ApprovalView(
        action_id=action_id, plan_sha256=record["plan_sha256"], action_json=raw, status="approved"
    )
    return item, record, inserted, ceremony


def test_real_registration_and_assertion_crypto_use_required_uv(settings):
    item, record, inserted, _ = service(settings)
    assert item.register("test", response("registration")).enrolled_credentials == 1
    assert inserted[0]["public_key"] == encode(COSE)
    assert item.approve("test", record["_id"], response()).status == "approved"


@pytest.mark.parametrize(
    "attack",
    [
        "origin",
        "rp_id",
        "challenge",
        "no_uv",
        "bad_signature",
        "wrong_user",
        "wrong_plan",
        "expired_plan",
    ],
)
def test_actual_approval_verifier_refuses_invalid_proofs(settings, attack):
    item, record, _, ceremony = service(settings)
    arguments = {}
    if attack == "origin":
        arguments["origin"] = "http://evil.invalid"
    if attack == "rp_id":
        arguments["rp_id"] = "evil.invalid"
    if attack == "challenge":
        arguments["challenge"] = b"not-bound-to-action"
    if attack == "no_uv":
        arguments["uv"] = False
    if attack == "bad_signature":
        arguments["tamper"] = True
    if attack == "wrong_user":
        arguments["user_handle"] = b"another-user"
    if attack == "wrong_plan":
        ceremony["plan_sha256"] = "f" * 64
    if attack == "expired_plan":
        typed = json.loads(record["action_json"])
        typed["expires_at"] = 1
        record["action_json"] = canonical(typed).decode()
    with pytest.raises(ValueError):
        item.approve("test", record["_id"], response(**arguments))


def test_challenge_is_expiring_single_use_and_bound_to_session():
    item = AuthorizationService.__new__(AuthorizationService)
    item.session = lambda cookie: {"_id": cookie}
    stored = {
        "session_id": "owner-session",
        "kind": "authentication",
        "expires_epoch": int(time.time()) + 60,
    }

    def consume(query):
        if stored and query["session_id"] == stored["session_id"]:
            result = copy.deepcopy(stored)
            stored.clear()
            return result
        return None

    item.client = SimpleNamespace(
        aegis=SimpleNamespace(auth_ceremonies=SimpleNamespace(find_one_and_delete=consume))
    )
    assertion = response()
    with pytest.raises(ValueError):
        item._consume("another-session", assertion, "authentication")
    assert stored
    item._consume("owner-session", assertion, "authentication")
    with pytest.raises(ValueError):
        item._consume("owner-session", assertion, "authentication")
    stored.update(session_id="owner-session", kind="authentication", expires_epoch=1)
    with pytest.raises(ValueError):
        item._consume("owner-session", assertion, "authentication")
