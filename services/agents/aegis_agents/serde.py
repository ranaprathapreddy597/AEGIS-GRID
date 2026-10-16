"""Primitive-only checkpoint codec. No pickle, dynamic imports or model constructors."""

import base64
import json
from typing import Any

from langgraph.types import Interrupt


def pack(value: Any) -> Any:
    if value is None or type(value) in (str, int, float, bool):
        return value
    if isinstance(value, bytes):
        return ["bytes", base64.b64encode(value).decode()]
    if isinstance(value, Interrupt):
        return ["interrupt", pack(value.value), value.id]
    if isinstance(value, tuple):
        return ["tuple", [pack(item) for item in value]]
    if isinstance(value, list):
        return ["list", [pack(item) for item in value]]
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        return ["dict", [[key, pack(item)] for key, item in value.items()]]
    raise ValueError("Unsupported checkpoint type")


def unpack(value: Any) -> Any:
    if not isinstance(value, list):
        return value
    kind = value[0]
    if kind == "bytes":
        return base64.b64decode(value[1], validate=True)
    if kind == "interrupt":
        return Interrupt(value=unpack(value[1]), id=value[2])
    if kind in {"list", "tuple"}:
        items = [unpack(item) for item in value[1]]
        return tuple(items) if kind == "tuple" else items
    if kind == "dict":
        return {key: unpack(item) for key, item in value[1]}
    raise ValueError("Unknown checkpoint encoding")


class SafeCheckpointJSON:
    def dumps_typed(self, obj: Any) -> tuple[str, bytes]:
        data = json.dumps(pack(obj), allow_nan=False, separators=(",", ":")).encode()
        if len(data) > 2_000_000:
            raise ValueError("Checkpoint size bound exceeded")
        return "aegis-json-v1", data

    def loads_typed(self, data: tuple[str, bytes]) -> Any:
        if data[0] != "aegis-json-v1" or len(data[1]) > 2_000_000:
            raise ValueError("Unknown or oversized checkpoint format")
        return unpack(json.loads(data[1]))
