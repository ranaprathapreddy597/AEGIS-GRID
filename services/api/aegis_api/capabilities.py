"""Fixed Ed25519 signed envelope. No algorithm negotiation or arbitrary audiences."""

import base64
import hashlib
import json
import os
import sys
import time

from aegis_agents.optimizer import canonical
from aegis_contracts.authorization import ExecutionEnvelope, ProposedPlan, VerifiedCapability
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


def encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def decode(value: str) -> bytes:
    if len(value) > 16384 or any(
        c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in value
    ):
        raise ValueError("Invalid base64url encoding")
    decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    if encode(decoded) != value:
        raise ValueError("Noncanonical base64url encoding")
    return decoded


def private_key(seed: str) -> Ed25519PrivateKey:
    if len(seed) < 32:
        raise ValueError("Strong local signing seed required")
    return Ed25519PrivateKey.from_private_bytes(hashlib.sha256(seed.encode()).digest())


def public_key(seed: str) -> str:
    return base64.b64encode(
        private_key(seed)
        .public_key()
        .public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    ).decode()


def sign(capability: VerifiedCapability, seed: str) -> str:
    payload = canonical(capability.model_dump())
    return encode(payload) + "." + encode(private_key(seed).sign(payload))


def verify(
    envelope: ExecutionEnvelope, public_spki: str
) -> tuple[ProposedPlan, VerifiedCapability]:
    parts = envelope.capability.split(".")
    if len(parts) != 2:
        raise ValueError("Invalid signed capability envelope")
    payload, signature = (decode(part) for part in parts)
    key = serialization.load_der_public_key(base64.b64decode(public_spki, validate=True))
    if not isinstance(key, Ed25519PublicKey):
        raise ValueError("Only Ed25519 keys accepted")
    try:
        key.verify(signature, payload)
    except InvalidSignature:
        raise ValueError("Capability signature refused") from None
    capability = VerifiedCapability.model_validate_json(payload)
    plan = ProposedPlan.model_validate_json(envelope.action_json)
    now = int(time.time())
    if not (capability.iat <= now + 2 and now < capability.exp <= capability.iat + 60):
        raise ValueError("Capability expired or outside bounded lifetime")
    if (
        capability.exp > plan.expires_at
        or now >= plan.expires_at
        or hashlib.sha256(envelope.action_json.encode()).hexdigest() != capability.plan_sha256
        or capability.action_id != plan.action_id
        or capability.resource_id != plan.resource_id
        or capability.expected_database_version != plan.expected_database_version
        or capability.expected_state_version != plan.expected_state_version
    ):
        raise ValueError("Capability does not authorize this immutable action/state")
    return plan, capability


if __name__ == "__main__":
    if sys.argv[1:] != ["public-key"]:
        raise SystemExit("Only local public-key derivation supported")
    print(json.dumps({"public_key": public_key(os.environ["AEGIS_CAPABILITY_SIGNING_SEED"])}))
