import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

from aegis_contracts.security import validate_token


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    viewer_token: SecretStr
    service_token: SecretStr
    seed: int = Field(default=42, ge=0, le=4294967295)
    edge_url: str = "http://edge:8001"
    twin_binary: Path = Path("/usr/local/bin/aegis-twin")

    @field_validator("viewer_token", "service_token")
    @classmethod
    def token_length(cls, value: SecretStr) -> SecretStr:
        validate_token(value.get_secret_value())
        return value

    @field_validator("edge_url")
    @classmethod
    def local_edge_only(cls, value: str) -> str:
        if value not in {"http://edge:8001", "http://127.0.0.1:8001", "http://localhost:8001"}:
            raise ValueError("Phase 1 supports only the local simulator edge")
        return value

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            viewer_token=SecretStr(os.environ.get("AEGIS_VIEWER_TOKEN", "")),
            service_token=SecretStr(os.environ.get("AEGIS_SERVICE_TOKEN", "")),
            seed=int(os.environ.get("AEGIS_SEED", "42")),
            edge_url=os.environ.get("AEGIS_EDGE_URL", "http://edge:8001"),
            twin_binary=Path(os.environ.get("AEGIS_TWIN_BINARY", "/usr/local/bin/aegis-twin")),
        )
