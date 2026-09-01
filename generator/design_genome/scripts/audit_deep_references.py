"""Live HTML status audit for the 20 non-Gold deep references."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

from ..data.deep_references import ADDITIONAL_DEEP_REFERENCES
from .build_reference_atlas import fetch


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "docs" / "design-encyclopedia" / "deep-reference-status.json"


class SignalParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.headings = 0
        self.images = 0
        self.navigation = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.headings += 1
        elif tag == "img":
            self.images += 1
        elif tag == "nav":
            self.navigation += 1


def inspect(item: tuple[str, str, str, str]) -> dict:
    name, url, sector, focus = item
    try:
        status, final_url, html = fetch(url, timeout=20)
        parser = SignalParser()
        parser.feed(html)
        return {
            "name": name, "url": url, "sector": sector, "focus": focus,
            "indexed": True, "html_inspected": True, "visual_inspected": False,
            "mobile_inspected": False, "gold_standard": False,
            "http_status": status, "final_url": final_url,
            "html_signals": {"headings": parser.headings, "images": parser.images, "navigation_landmarks": parser.navigation},
            "note": "HTML structure inspected; visual and mobile behavior not inspected.",
        }
    except Exception as error:  # Research failures are evidence, not build failures.
        return {
            "name": name, "url": url, "sector": sector, "focus": focus,
            "indexed": True, "html_inspected": False, "visual_inspected": False,
            "mobile_inspected": False, "gold_standard": False,
            "http_status": None, "final_url": None, "html_signals": {},
            "note": f"Live HTML inspection unavailable: {type(error).__name__}.",
        }


def main() -> None:
    with ThreadPoolExecutor(max_workers=8) as pool:
        references = list(pool.map(inspect, ADDITIONAL_DEEP_REFERENCES))
    payload = {
        "schema_version": 1, "audited_at": date.today().isoformat(),
        "scope": "20 focused non-Gold references; status does not imply visual inspection.",
        "counts": {"total": len(references), "html_inspected": sum(item["html_inspected"] for item in references)},
        "references": references,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["counts"]))


if __name__ == "__main__":
    main()
