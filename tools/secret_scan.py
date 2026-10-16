"""Small repository baseline scanner; not a substitute for a security audit."""

import re
import subprocess
from pathlib import Path

from dev import ROOT, SECRET_NAMES, read_env


def main() -> None:
    paths = (
        subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT
        )
        .decode()
        .split("\0")
    )
    actual_secrets = [
        value
        for key, value in read_env().items()
        if (key in SECRET_NAMES or key.endswith(("API_KEY", "TOKEN", "PASSWORD")))
        and len(value) >= 16
    ]
    leaked = []
    for relative in filter(None, paths):
        path = ROOT / Path(relative)
        if not path.is_file() or path.suffix in {".png", ".jpg", ".webm", ".pdf"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(secret in text for secret in actual_secrets) or re.search(
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", text
        ):
            leaked.append(relative)
    if leaked:
        raise SystemExit("Secret material found in: " + ", ".join(leaked))
    print(
        f"PASS: scanned {len(list(filter(None, paths)))} repository files; "
        "no local tokens/private keys found"
    )


if __name__ == "__main__":
    main()
