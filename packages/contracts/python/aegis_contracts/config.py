import os
from pathlib import Path
from typing import Literal, cast
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

from aegis_contracts.security import validate_token


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    viewer_token: SecretStr
    service_token: SecretStr
    seed: int = Field(default=42, ge=0, le=4294967295)
    scenario_id: str = Field(default="scenario-000", pattern=r"^scenario-0\d{2}$")
    scenario_dir: Path = Path("data/scenarios")
    time_scale: float = Field(default=1.0, ge=0.5, le=20, allow_inf_nan=False)
    edge_url: str = "http://edge:8001"
    twin_binary: Path = Path("/usr/local/bin/aegis-twin")
    twin_library: Path = Path("/usr/local/lib/libaegis_twin.so")
    safety_mode: Literal["enforce", "observe_only"] = "enforce"
    memory_capacity: int = Field(default=256, ge=32, le=4096)
    cloud_events_url: str | None = None
    cloud_token: SecretStr | None = None
    storage_enabled: bool = False
    mongo_writer_password: SecretStr | None = None
    mongo_reader_password: SecretStr | None = None
    redis_writer_password: SecretStr | None = None
    ingest_token: SecretStr | None = None
    graph_password: SecretStr | None = None
    approver_token: SecretStr | None = None
    approver_password: SecretStr | None = None
    gateway_password: SecretStr | None = None
    executor_token: SecretStr | None = None
    gateway_token: SecretStr | None = None
    signing_seed: SecretStr | None = None
    capability_public_key: str = ""
    approval_origin: str = "http://localhost:8080"

    @field_validator("approval_origin")
    @classmethod
    def loopback_approval_origin(cls, value: str) -> str:
        parsed = urlsplit(value)
        if (
            parsed.scheme != "http"
            or parsed.hostname != "localhost"
            or parsed.username
            or parsed.password
            or parsed.path
            or parsed.query
            or parsed.fragment
            or parsed.port is None
            or not 1024 <= parsed.port <= 65535
        ):
            raise ValueError("Local passkeys require an explicit http://localhost:PORT origin")
        return value

    @field_validator("cloud_events_url")
    @classmethod
    def cloud_tls_only(cls, value: str | None) -> str | None:
        if value is not None:
            parts = urlsplit(value)
            if (
                parts.scheme != "https"
                or not parts.hostname
                or parts.username
                or parts.password
                or parts.query
                or parts.fragment
                or parts.path != "/api/v1/edge/events"
            ):
                raise ValueError(
                    "Cloud requires explicit HTTPS AEGIS events URL without credentials"
                )
        return value

    @field_validator("viewer_token", "service_token")
    @classmethod
    def token_length(cls, value: SecretStr) -> SecretStr:
        validate_token(value.get_secret_value())
        return value

    @field_validator("edge_url")
    @classmethod
    def local_edge_only(cls, value: str) -> str:
        if value not in {"http://edge:8001", "http://127.0.0.1:8001", "http://localhost:8001"}:
            raise ValueError("Only the local simulator edge is supported")
        return value

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            approver_token=SecretStr(os.environ["AEGIS_APPROVER_TOKEN"])
            if os.environ.get("AEGIS_APPROVER_TOKEN")
            else None,
            approver_password=SecretStr(os.environ["AEGIS_APPROVER_PASSWORD"])
            if os.environ.get("AEGIS_APPROVER_PASSWORD")
            else None,
            gateway_password=SecretStr(os.environ["AEGIS_GATEWAY_PASSWORD"])
            if os.environ.get("AEGIS_GATEWAY_PASSWORD")
            else None,
            executor_token=SecretStr(os.environ["AEGIS_EXECUTOR_TOKEN"])
            if os.environ.get("AEGIS_EXECUTOR_TOKEN")
            else None,
            gateway_token=SecretStr(os.environ["AEGIS_GATEWAY_TOKEN"])
            if os.environ.get("AEGIS_GATEWAY_TOKEN")
            else None,
            signing_seed=SecretStr(os.environ["AEGIS_CAPABILITY_SIGNING_SEED"])
            if os.environ.get("AEGIS_CAPABILITY_SIGNING_SEED")
            else None,
            capability_public_key=os.environ.get("AEGIS_CAPABILITY_PUBLIC_KEY", ""),
            approval_origin=os.environ.get("AEGIS_APPROVAL_ORIGIN", "http://localhost:8080"),
            graph_password=SecretStr(os.environ["AEGIS_GRAPH_PASSWORD"])
            if os.environ.get("AEGIS_GRAPH_PASSWORD")
            else None,
            viewer_token=SecretStr(os.environ.get("AEGIS_VIEWER_TOKEN", "")),
            service_token=SecretStr(os.environ.get("AEGIS_SERVICE_TOKEN", "")),
            seed=int(os.environ.get("AEGIS_SEED", "42")),
            scenario_id=os.environ.get("AEGIS_SCENARIO", "scenario-000"),
            time_scale=float(os.environ.get("AEGIS_TIME_SCALE", "1")),
            edge_url=os.environ.get("AEGIS_EDGE_URL", "http://edge:8001"),
            twin_binary=Path(os.environ.get("AEGIS_TWIN_BINARY", "/usr/local/bin/aegis-twin")),
            twin_library=Path(
                os.environ.get("AEGIS_TWIN_LIBRARY", "/usr/local/lib/libaegis_twin.so")
            ),
            safety_mode=cast(
                Literal["enforce", "observe_only"], os.environ.get("AEGIS_SAFETY_MODE", "enforce")
            ),
            memory_capacity=int(os.environ.get("AEGIS_EDGE_MEMORY_CAPACITY", "256")),
            cloud_events_url=os.environ.get("AEGIS_CLOUD_EVENTS_URL") or None,
            cloud_token=SecretStr(os.environ["AEGIS_CLOUD_EVENTS_TOKEN"])
            if os.environ.get("AEGIS_CLOUD_EVENTS_TOKEN")
            else None,
            storage_enabled=os.environ.get("AEGIS_STORAGE_ENABLED", "false").lower() == "true",
            mongo_writer_password=SecretStr(os.environ["AEGIS_MONGO_WRITER_PASSWORD"])
            if os.environ.get("AEGIS_MONGO_WRITER_PASSWORD")
            else None,
            mongo_reader_password=SecretStr(os.environ["AEGIS_MONGO_READER_PASSWORD"])
            if os.environ.get("AEGIS_MONGO_READER_PASSWORD")
            else None,
            redis_writer_password=SecretStr(os.environ["AEGIS_REDIS_WRITER_PASSWORD"])
            if os.environ.get("AEGIS_REDIS_WRITER_PASSWORD")
            else None,
            ingest_token=SecretStr(os.environ["AEGIS_INGEST_TOKEN"])
            if os.environ.get("AEGIS_INGEST_TOKEN")
            else None,
        )
