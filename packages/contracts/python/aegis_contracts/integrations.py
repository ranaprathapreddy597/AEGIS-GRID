from typing import Annotated, Literal

from pydantic import Field

from aegis_contracts.models import Contract
from aegis_contracts.optimization import Digest


class MCPServerMetadata(Contract):
    server_id: str
    name: Annotated[str, Field(max_length=128)]
    configured_tool_names: Annotated[list[str], Field(max_length=64)]
    disabled: bool
    invocation_schemas_verified: Literal[False] = False


class IntegrationGate(Contract):
    provider: str
    status: Literal["BLOCKED", "verified_local"]
    reason: str


class IntegrationStatus(Contract):
    gates: list[IntegrationGate]
    evolus_spec_sha256: Digest
    verified_evolus_mcp_invocation_tools: Literal[0] = 0
    external_mutations_enabled: Literal[False] = False


class RepairBundle(Contract):
    artifact_sha256: Digest
    target_path: Literal["apps/web/src/ApprovalPanel.tsx"] = "apps/web/src/ApprovalPanel.tsx"
    base_revision: Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
    before_sha256: Digest
    after_sha256: Digest
    patch_sha256: Digest
    patch: Annotated[str, Field(max_length=65536)]
    problem: str
    local_browser_regression_verified: Literal[True] = True
    patch_apply_verified: Literal[True] = True
    before_probe: dict[str, str | bool]
    after_probe: dict[str, str | bool]
    hosted_ci_verified: Literal[False] = False
    remote_publication: Literal["BLOCKED"] = "BLOCKED"
    reason: str
