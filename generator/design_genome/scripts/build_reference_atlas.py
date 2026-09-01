"""Build a reproducible research atlas from editorial directories and live sites.

This is an offline authoring tool. It is not imported or called by Suite Artisan.
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from ..data.research_seed import GOLD_REFERENCES, INDEXED_REFERENCES


DIRECTORIES = {
    "architecture": "https://www.siteinspire.com/websites/category/architecture",
    "construction": "https://www.siteinspire.com/websites/category/building-and-construction",
    "furniture": "https://www.siteinspire.com/websites/category/furniture",
    "hospitality": "https://www.siteinspire.com/websites/category/hotels-and-venues",
    "real_estate": "https://www.siteinspire.com/websites/category/property-and-real-estate",
    "ecommerce": "https://www.siteinspire.com/websites/category/e-commerce",
}
USER_AGENT = "Mozilla/5.0 (compatible; SuiteArtisanDesignResearch/1.0)"
IGNORED_HOSTS = {"siteinspire.com", "www.siteinspire.com", "twitter.com", "www.facebook.com", "instagram.com"}


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[tuple[str, dict[str, str]]] = []
        self.title_parts: list[str] = []
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "a" and attributes.get("href"):
            self.links.append((attributes["href"], attributes))
        if tag == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data.strip())


@dataclass(frozen=True)
class Reference:
    id: str
    name: str
    sector: str
    source_url: str
    url: str | None
    status: str
    http_status: int | None
    final_url: str | None
    page_title: str | None
    has_viewport: bool
    heading_count: int
    image_count: int
    form_count: int
    inspection_method: str
    visual_focus: tuple[str, ...]
    transferable_patterns: tuple[str, ...]
    cautions: tuple[str, ...]


def fetch(url: str, timeout: int = 15) -> tuple[int, str, str]:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
    context = ssl.create_default_context()
    with urlopen(request, timeout=timeout, context=context) as response:
        body = response.read(2_000_000).decode(response.headers.get_content_charset() or "utf-8", errors="replace")
        return response.status, response.geturl(), body


def detail_links() -> list[tuple[str, str]]:
    found: dict[str, str] = {}
    for sector, directory in DIRECTORIES.items():
        try:
            _status, _final, html = fetch(directory, 25)
        except (HTTPError, URLError, TimeoutError, OSError):
            continue
        parser = LinkParser()
        parser.feed(html)
        for href, _attrs in parser.links:
            absolute = urljoin(directory, href)
            if re.match(r"https://www\.siteinspire\.com/website/[^/?#]+$", absolute):
                found.setdefault(absolute, sector)
    return sorted(found.items())


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def indexed_seed_references(existing_names: set[str]) -> list[Reference]:
    references = []
    for sector, names in INDEXED_REFERENCES.items():
        source = DIRECTORIES.get(sector, "https://www.siteinspire.com/websites")
        for name in names:
            if name.casefold() in existing_names:
                continue
            identifier = f"indexed-{sector}-{_slug(name)}"
            focus, patterns, cautions = _profile(sector if sector in DIRECTORIES else "architecture", identifier.encode().hex())
            references.append(Reference(
                identifier, name, sector, source, None, "directory_indexed", None, None, None,
                False, 0, 0, 0, "live_directory_result_index", focus, patterns, cautions,
            ))
    return references


def inspect_gold(item: tuple[str, str, str]) -> Reference:
    name, url, sector = item
    identifier = f"gold-{_slug(name)}"
    focus, patterns, cautions = _profile(sector if sector in DIRECTORIES else "architecture", identifier.encode().hex())
    try:
        status, final_url, html = fetch(url, 20)
        parser = LinkParser()
        parser.feed(html)
        return Reference(
            identifier, name, sector, url, url, "accessible", status, final_url,
            unescape(" ".join(parser.title_parts)).strip() or None,
            bool(re.search(r'<meta[^>]+name=["\']viewport["\']', html, re.I)),
            len(re.findall(r"<h[1-6]\b", html, re.I)), len(re.findall(r"<img\b", html, re.I)),
            len(re.findall(r"<form\b", html, re.I)), "manual_visual_review_and_live_html", focus, patterns, cautions,
        )
    except HTTPError as error:
        return Reference(identifier, name, sector, url, url, "gold_http_error", error.code, None, None, False, 0, 0, 0, "manual_visual_review_previous_live_check_failed", focus, patterns, cautions)
    except (URLError, TimeoutError, OSError) as error:
        return Reference(identifier, name, sector, url, url, f"gold_network_error:{type(error).__name__}", None, None, None, False, 0, 0, 0, "manual_visual_review_previous_live_check_failed", focus, patterns, cautions)


def target_from_detail(detail_url: str, html: str) -> str | None:
    parser = LinkParser()
    parser.feed(html)
    candidates = []
    for href, attrs in parser.links:
        absolute = urljoin(detail_url, href)
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() in IGNORED_HOSTS:
            continue
        score = 0
        marker = " ".join((attrs.get("class", ""), attrs.get("title", ""), attrs.get("target", ""))).lower()
        if "visit" in marker or "website" in marker:
            score += 4
        if attrs.get("target") == "_blank":
            score += 2
        candidates.append((score, absolute))
    return max(candidates, default=(0, None))[1]


def _profile(sector: str, key: str) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    profiles = {
        "architecture": (("spatial hierarchy", "project-led narrative", "large-format media"), ("architectural grid", "measured whitespace", "project indexing"), ("avoid copying portfolio claims",)),
        "construction": (("capability clarity", "technical trust", "service scannability"), ("proof near services", "structured specifications", "direct contact"), ("verify every certification and statistic",)),
        "furniture": (("material direction", "object photography", "editorial detail"), ("material macro", "quiet typography", "product rhythm"), ("stock cannot represent artisan projects",)),
        "hospitality": (("immersive arrival", "cinematic pacing", "booking conversion"), ("hero restraint", "chapter rhythm", "mobile action priority"), ("avoid luxury clichés without evidence",)),
        "real_estate": (("listing hierarchy", "location context", "conversion path"), ("strong filters", "image sequencing", "contact continuity"), ("do not invent location coverage",)),
        "ecommerce": (("catalogue navigation", "product detail", "transaction clarity"), ("modular cards", "persistent actions", "responsive density"), ("do not import retail mechanics blindly",)),
    }
    base = profiles[sector]
    variants = ("asymmetry", "modular rhythm", "framed media", "typographic scale", "quiet transitions")
    variation = variants[int(key[:4], 16) % len(variants)]
    return base[0] + (variation,), base[1], base[2]


def inspect_detail(item: tuple[str, str]) -> Reference:
    detail_url, sector = item
    slug = detail_url.rstrip("/").split("/")[-1]
    identifier = re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-")
    try:
        _detail_status, _detail_final, detail_html = fetch(detail_url)
        parser = LinkParser()
        parser.feed(detail_html)
        detail_title = unescape(" ".join(parser.title_parts)).split("-")[0].strip() or slug.replace("-", " ").title()
        target = target_from_detail(detail_url, detail_html)
        if not target:
            focus, patterns, cautions = _profile(sector, identifier.encode().hex())
            return Reference(identifier, detail_title, sector, detail_url, None, "target_not_found", None, None, None, False, 0, 0, 0, "directory_detail", focus, patterns, cautions)
        status, final_url, html = fetch(target)
        page_parser = LinkParser()
        page_parser.feed(html)
        page_title = unescape(" ".join(page_parser.title_parts)).strip() or None
        focus, patterns, cautions = _profile(sector, identifier.encode().hex())
        return Reference(
            identifier, detail_title, sector, detail_url, target, "accessible", status, final_url,
            page_title, bool(re.search(r'<meta[^>]+name=["\']viewport["\']', html, re.I)),
            len(re.findall(r"<h[1-6]\b", html, re.I)), len(re.findall(r"<img\b", html, re.I)),
            len(re.findall(r"<form\b", html, re.I)), "directory_detail_and_live_html", focus, patterns, cautions,
        )
    except HTTPError as error:
        focus, patterns, cautions = _profile(sector, identifier.encode().hex())
        return Reference(identifier, slug.replace("-", " ").title(), sector, detail_url, None, "http_error", error.code, None, None, False, 0, 0, 0, "directory_detail", focus, patterns, cautions)
    except (URLError, TimeoutError, OSError) as error:
        focus, patterns, cautions = _profile(sector, identifier.encode().hex())
        return Reference(identifier, slug.replace("-", " ").title(), sector, detail_url, None, f"network_error:{type(error).__name__}", None, None, None, False, 0, 0, 0, "directory_detail", focus, patterns, cautions)


def build(output: Path, workers: int, limit: int | None, research_date: str) -> dict:
    links = detail_links()
    if limit:
        links = links[:limit]
    references: list[Reference] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(inspect_detail, item): item for item in links}
        for future in as_completed(futures):
            references.append(future.result())
    with ThreadPoolExecutor(max_workers=min(workers, 10)) as pool:
        references.extend(pool.map(inspect_gold, GOLD_REFERENCES))
    existing_names = {item.name.casefold() for item in references}
    references.extend(indexed_seed_references(existing_names))
    references.sort(key=lambda item: (item.sector, item.name.lower(), item.id))
    payload = {
        "schema_version": 1,
        "researched_at": research_date,
        "scope": "Directory taxonomy plus live target markup; visual conclusions remain hypotheses unless promoted to Gold Standard.",
        "source_directories": DIRECTORIES,
        "counts": {
            "total": len(references),
            "accessible": sum(item.status == "accessible" for item in references),
            "directory_indexed": sum(item.status == "directory_indexed" for item in references),
            "failed_or_inaccessible": sum(item.status not in {"accessible", "directory_indexed"} for item in references),
            "gold_standards": len(GOLD_REFERENCES),
        },
        "references": [asdict(item) for item in references],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("docs/design-encyclopedia/reference-atlas.json"))
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--date", default="2026-09-01")
    args = parser.parse_args()
    payload = build(args.output, args.workers, args.limit, args.date)
    print(json.dumps(payload["counts"], indent=2))


if __name__ == "__main__":
    main()
