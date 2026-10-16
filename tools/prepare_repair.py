"""Build a real reviewed local patch bundle from executed browser regression proof."""

import difflib
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from aegis_agents.optimizer import digest
from aegis_contracts.integrations import RepairBundle

TARGET = "apps/web/src/ApprovalPanel.tsx"


def main() -> None:
    before_probe = json.loads(Path("docs/results/phase10-repair-before.json").read_text("utf-8"))
    after_probe = json.loads(Path("docs/results/phase10-repair-after.json").read_text("utf-8"))
    if before_probe["resumed"] is not False or after_probe["resumed"] is not True:
        raise RuntimeError("Actual before/after browser regression evidence required")
    revision = subprocess.check_output(["git", "rev-parse", "d8ed0bd"], text=True).strip()
    before = subprocess.check_output(["git", "show", f"{revision}:{TARGET}"])
    after = Path("data/repairs/approval-session-after.tsx").read_bytes()
    if after_probe.get("source_sha256") != hashlib.sha256(after).hexdigest():
        raise RuntimeError("Browser proof must bind the exact standalone repair candidate")
    patch = "".join(
        difflib.unified_diff(
            before.decode().splitlines(keepends=True),
            after.decode().splitlines(keepends=True),
            fromfile="a/" + TARGET,
            tofile="b/" + TARGET,
        )
    )
    if not patch:
        raise RuntimeError("Actual reviewed source change required")
    with tempfile.TemporaryDirectory(prefix="aegis-reviewed-patch-") as directory:
        root = Path(directory)
        target = root / TARGET
        target.parent.mkdir(parents=True)
        target.write_bytes(before)
        diff = root / "repair.diff"
        diff.write_text(patch, encoding="utf-8", newline="\n")
        subprocess.run(
            ["git", "-c", "core.autocrlf=false", "apply", "--check", str(diff)],
            cwd=root,
            check=True,
        )
        subprocess.run(
            ["git", "-c", "core.autocrlf=false", "apply", str(diff)], cwd=root, check=True
        )
        if target.read_bytes() != after:
            raise RuntimeError("Reviewed patch does not reproduce exact source")
    report = RepairBundle(
        artifact_sha256="0" * 64,
        base_revision=revision,
        before_sha256=hashlib.sha256(before).hexdigest(),
        after_sha256=hashlib.sha256(after).hexdigest(),
        patch_sha256=hashlib.sha256(patch.encode()).hexdigest(),
        patch=patch,
        problem=(
            "Browser refresh lost the owner session and paused proposal; "
            "restore real API state without retaining a browser token."
        ),
        before_probe=before_probe,
        after_probe=after_probe,
        reason="Remote scope, publication approval and hosted CI are not verified",
    )
    value = report.model_dump()
    value.pop("artifact_sha256")
    report = report.model_copy(update={"artifact_sha256": digest(value)})
    destination = Path("data/repairs")
    destination.mkdir(exist_ok=True)
    (destination / "approval-session.json").write_text(
        report.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    (destination / "approval-session.diff").write_text(patch, encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "local_patch_apply": "PASS",
                "browser_regression": "PASS",
                "artifact_sha256": report.artifact_sha256,
                "remote_publication": "BLOCKED",
            }
        )
    )


if __name__ == "__main__":
    main()
