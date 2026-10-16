"""Trusted parser worker for a network-none, read-only, memory-bounded container."""

import json
import sys

from pypdf import PdfReader


def main() -> None:
    reader = PdfReader("/input/document.pdf", strict=True)
    if reader.is_encrypted or not 1 <= len(reader.pages) <= 64:
        raise ValueError("Unsupported PDF")
    root = reader.trailer["/Root"]
    names = root.get("/Names", {})
    if hasattr(names, "get_object"):
        names = names.get_object()
    if "/EmbeddedFiles" in names or "/JavaScript" in names:
        raise ValueError("Active/embedded PDF content refused")
    action = root.get("/OpenAction")
    if hasattr(action, "get_object"):
        action = action.get_object()
    if isinstance(action, dict) and action.get("/S") in {"/JavaScript", "/Launch"}:
        raise ValueError("Active PDF action refused")
    pages = []
    for number in [1, 2, 7, 8, 16, 17, 18]:
        if number > len(reader.pages):
            continue
        page = reader.pages[number - 1]
        if page.get("/AA"):
            raise ValueError("Additional PDF actions refused")
        text = page.extract_text() or ""
        if len(text) > 16000:
            raise ValueError("Page exceeds bound")
        pages.append({"page": number, "text": text})
    if sum(len(p["text"]) for p in pages) > 100000:
        raise ValueError("Text exceeds bound")
    print(json.dumps({"page_count": len(reader.pages), "pages": pages}))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"status": "BLOCKED", "error_class": type(error).__name__}))
        sys.exit(1)
