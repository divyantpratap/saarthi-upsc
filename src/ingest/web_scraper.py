"""Scrape UPSC-relevant web pages into plain text documents."""
from __future__ import annotations

import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from settings import SAMPLE_URLS_FILE, SCRAPED_DIR

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; UPSCStudyBot/1.0; +https://example.com/bot)"
    )
}


def _clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def scrape_url(url: str, timeout: int = 20) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return _clean_html(resp.text)
    except Exception as exc:
        print(f"  [skip] {url}: {exc}")
        return None


def load_urls_from_file(path: Path | None = None) -> list[str]:
    path = path or SAMPLE_URLS_FILE
    if not path.exists():
        return []
    urls = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


def scrape_urls(urls: list[str], save_dir: Path | None = None) -> list[dict]:
    """Scrape URLs and optionally save raw text to disk."""
    save_dir = save_dir or SCRAPED_DIR
    save_dir.mkdir(parents=True, exist_ok=True)

    documents: list[dict] = []
    for i, url in enumerate(urls):
        text = scrape_url(url)
        if not text or len(text) < 100:
            continue
        slug = re.sub(r"[^\w]+", "_", url[-60:])[:50]
        out_file = save_dir / f"page_{i}_{slug}.txt"
        out_file.write_text(text, encoding="utf-8")
        documents.append(
            {
                "text": text,
                "source": f"web:{url}",
                "metadata": {"type": "web", "url": url},
            }
        )
    return documents


def scrape_urls_from_file(urls_file: Path | None = None) -> list[dict]:
    urls = load_urls_from_file(urls_file)
    if not urls:
        print("No URLs in sample_urls.txt — skipping web scrape.")
    return scrape_urls(urls)
