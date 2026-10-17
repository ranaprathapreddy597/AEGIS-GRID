"""Reproduce named attacks using existing real native/crypto tests, without providers."""

import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    "Sensor spoofing": (
        "tests/integration/test_edge_safety.py::"
        "test_real_spoof_fault_detected_and_local_stop_latches_without_any_cloud",
        "Native hidden heating versus delivered spoofed measurement; local stop latches offline.",
    ),
    "Conflicting manuals": (
        "tests/unit/test_manual_evidence.py::"
        "test_actual_thousand_page_corpus_has_verifiable_limits_and_contradiction",
        "Whole original corpus conflict refuses operational authorization.",
    ),
    "Malicious retrieved instructions": (
        "tests/unit/test_manual_evidence.py::"
        "test_injected_pdf_instructions_are_untrusted_data_without_commands",
        "Original malicious PDF instruction cannot become command or trusted revision.",
    ),
    "Unsafe proposal": (
        "tests/security/test_capability_authorization.py::"
        "test_signed_unsafe_or_modified_action_cannot_override_independent_schema_policy",
        "Even a signed unsafe control is rejected by independent typed policy.",
    ),
    "Stale approved state": (
        "tests/integration/test_authorization_gateway.py::"
        "test_protected_gateway_refuses_before_any_state_change[stale_database]",
        "Real signed capability/native gateway; resource/approval storage uses explicit doubles.",
    ),
    "Invalid WebAuthn proofs": (
        "tests/security/test_webauthn_proofs.py::test_actual_approval_verifier_refuses_invalid_proofs",
        "Real WebAuthn crypto verifies origin, UV, proof and plan binding; storage doubles.",
    ),
}


def main() -> None:
    directory = ROOT / ".run/sprint-adversary"
    directory.mkdir(parents=True, exist_ok=True)
    checks = []
    image = "aegis-grid-qa:phase12"
    image_id = subprocess.check_output(
        ["docker", "image", "inspect", "--format", "{{.Id}}", image], text=True
    ).strip()
    for index, (name, (selector, reason)) in enumerate(CASES.items()):
        junit = directory / f"case-{index}.xml"
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--mount",
                f"type=bind,source={directory},target=/proof",
                image,
                "python",
                "-m",
                "pytest",
                "-q",
                selector,
                f"--junitxml=/proof/case-{index}.xml",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        (directory / f"case-{index}.txt").write_text(
            result.stdout + result.stderr, encoding="utf-8"
        )
        nodes = ET.parse(junit).getroot().findall(".//testcase") if junit.exists() else []  # noqa: S314 - local pytest output
        passed = sum(
            not any(n.tag in {"failure", "error", "skipped"} for n in node) for node in nodes
        )
        checks.append(
            {
                "name": name,
                "state": "PASS" if result.returncode == 0 and passed else "FAIL",
                "passed": passed,
                "selector": selector,
                "reason": reason,
                "test_source_sha256": hashlib.sha256(
                    (ROOT / selector.split("::")[0]).read_bytes()
                ).hexdigest(),
            }
        )
    report = {
        "scope": (
            "Offline deterministic native/crypto attack regression; no hosted calls or plant writes"
        ),
        "image_id": image_id,
        "state": "PASS" if all(row["state"] == "PASS" for row in checks) else "FAIL",
        "checks": checks,
        "limitations": [
            "Finite selected attacks, not a security certification.",
            "Stale approval uses a signed capability and storage doubles; "
            "historical browser proof remains separate.",
        ],
    }
    (ROOT / "docs/results/SPRINT_ADVERSARY.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    if report["state"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
