"""Public mock-test listing discovery. Question content is never copied."""
from __future__ import annotations

from dataclasses import dataclass, asdict

import requests
from bs4 import BeautifulSoup


SOURCES = {
    "Drishti IAS": "https://www.drishtiias.com/upsc-all-india-prelims-open-mock-test",
    "MockTestZone": "https://www.mocktestzone.in/upsc-mock-tests",
}


@dataclass(frozen=True)
class ExternalTest:
    provider: str
    title: str
    url: str
    test_type: str
    detail: str = ""


def fetch_external_tests(timeout: int = 8) -> list[dict]:
    """Read only titles/links visible on providers' public listing pages."""
    tests: list[ExternalTest] = []
    for provider, url in SOURCES.items():
        try:
            response = requests.get(url, timeout=timeout, headers={"User-Agent": "Saarthi-UPSC/1.0"})
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            if provider == "MockTestZone":
                for heading in soup.select("h3"):
                    title = " ".join(heading.get_text(" ", strip=True).split())
                    if not title or len(title) > 120:
                        continue
                    link = heading.find_next("a", href=True)
                    if not link:
                        continue
                    href = requests.compat.urljoin(url, link["href"])
                    kind = "Sectional" if any(x in title.lower() for x in ("csat", "section", "subject")) else "Full Length"
                    tests.append(ExternalTest(provider, title, href, kind, "Hosted by MockTestZone"))
            else:
                tests.append(ExternalTest(provider, "Pre Prayaas — All India Open Mock", url, "Full Length", "GS-I + CSAT · 120 minutes each"))
        except requests.RequestException:
            continue
    return [asdict(test) for test in tests[:16]]
