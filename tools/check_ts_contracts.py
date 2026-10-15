import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    pnpm = shutil.which("pnpm")
    if not pnpm:
        raise SystemExit("pnpm is required")
    with tempfile.TemporaryDirectory(prefix="aegis-contract-") as temp:
        output = Path(temp) / "api.d.ts"
        subprocess.run(
            [
                pnpm,
                "exec",
                "openapi-typescript",
                "packages/contracts/generated/openapi.json",
                "-o",
                str(output),
            ],
            cwd=ROOT,
            check=True,
        )
        expected = ROOT / "packages/contracts/generated/api.d.ts"
        if output.read_text() != expected.read_text():
            raise SystemExit("TypeScript contract drift: run pnpm contracts")
    print("TypeScript contracts match")


if __name__ == "__main__":
    main()
