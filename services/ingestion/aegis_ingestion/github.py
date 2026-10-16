"""Verified GitHub read preflight and reviewed publication draft; remote writes closed."""

import base64
import re
from typing import Any
from urllib.parse import quote

import httpx
from pydantic import SecretStr


class ExternalGateBlocked(RuntimeError):
    pass


class GitHubRepairGateway:
    def __init__(
        self,
        token: SecretStr,
        owner: str,
        repository: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not all(
            re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9_.-]{0,99}", value)
            for value in (owner, repository)
        ):
            raise ValueError("Explicit GitHub repository scope required")
        self.prefix = f"/repos/{owner}/{repository}"
        self.client = httpx.AsyncClient(
            base_url="https://api.github.com",
            timeout=10,
            follow_redirects=False,
            trust_env=False,
            transport=transport,
            headers={
                "Authorization": "Bearer " + token.get_secret_value(),
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def read_base(self, branch: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_./-]{0,119}", branch) or ".." in branch:
            raise ValueError("Explicit safe branch required")
        try:
            async with self.client.stream(
                "GET", self.prefix + "/git/ref/heads/" + quote(branch, safe="")
            ) as response:
                if response.status_code != 200:
                    raise ExternalGateBlocked("GitHub read/auth preflight refused")
                body = bytearray()
                async for data in response.aiter_bytes():
                    body.extend(data)
                    if len(body) > 131072:
                        raise ExternalGateBlocked("GitHub response exceeds local bound")
                import json

                value = json.loads(body)
                sha = value["object"]["sha"]
                if (
                    value["ref"] != "refs/heads/" + branch
                    or value["object"]["type"] != "commit"
                    or not isinstance(sha, str)
                    or not re.fullmatch(r"[0-9a-f]{40}", sha)
                ):
                    raise ExternalGateBlocked("GitHub ref identity/schema refused")
                return sha
        except (httpx.HTTPError, KeyError, ValueError, TypeError):
            raise ExternalGateBlocked("GitHub preflight unavailable or invalid") from None

    def publication_draft(
        self,
        *,
        base_sha: str,
        base_blob_sha: str,
        base_branch: str,
        after_source: bytes,
        artifact_sha256: str,
    ) -> list[dict[str, Any]]:
        if (
            not re.fullmatch(r"[0-9a-f]{40}", base_sha)
            or not re.fullmatch(r"[0-9a-f]{40}", base_blob_sha)
            or not re.fullmatch(r"[0-9a-f]{64}", artifact_sha256)
            or len(after_source) > 65536
        ):
            raise ValueError("Verified immutable revision/blob/artifact bounds required")
        branch = "codex/approval-repair-" + artifact_sha256[:12]
        if (
            not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_./-]{0,119}", base_branch)
            or ".." in base_branch
        ):
            raise ValueError("Explicit base branch required")
        return [
            {
                "step": "create_branch",
                "method": "POST",
                "path": self.prefix + "/git/refs",
                "body": {"ref": "refs/heads/" + branch, "sha": base_sha},
            },
            {
                "step": "commit_exact_reviewed_file",
                "method": "PUT",
                "path": self.prefix + "/contents/apps/web/src/ApprovalPanel.tsx",
                "body": {
                    "branch": branch,
                    "sha": base_blob_sha,
                    "message": "Restore reviewed approval session after browser reload",
                    "content": base64.b64encode(after_source).decode(),
                },
            },
            {
                "step": "require_ci_and_review",
                "remote_write": False,
                "required": "Verified required checks on the exact new commit",
            },
            {
                "step": "open_review_pr",
                "method": "POST",
                "path": self.prefix + "/pulls",
                "body": {
                    "head": branch,
                    "title": "Restore immutable approval after browser reload",
                    "draft": True,
                    "base": base_branch,
                },
                "requires": "Explicit approved base branch; verified CI; publication capability",
            },
        ]

    async def publish(self, draft: object, capability: str) -> None:
        # The current capability policy has no GitHub action scope. No HTTP write
        # is reachable, even if a read token or plausible model text is supplied.
        raise ExternalGateBlocked(
            "GitHub publication BLOCKED: remote scope/approval/CI not verified"
        )
