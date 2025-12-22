from __future__ import annotations

from datetime import datetime
from typing import Dict, List
import xml.etree.ElementTree as ET
import requests

Paper = Dict[str, object]  # {"title": str, "summary": str, "year": int}

class ArxivProvider:
    """
    arXiv Atom API:
      GET https://export.arxiv.org/api/query
        ?search_query=all:<query>
        &start=0
        &max_results=<limit>
    """
    BASE_URL = "https://export.arxiv.org/api/query"

    def __init__(self, timeout_s: int = 10) -> None:
        self.timeout_s = timeout_s

    def search(self, query: str, limit: int = 5) -> List[Paper]:
        query = (query or "").strip()
        if not query:
            return []

        limit = max(1, min(int(limit), 5))

        params = {"search_query": f"all:{query}", "start": 0, "max_results": limit}
        headers = {"User-Agent": "literature-surveyor/phase4"}

        try:
            resp = requests.get(self.BASE_URL, params=params, headers=headers, timeout=self.timeout_s)
            resp.raise_for_status()
            xml_text = resp.text
        except Exception:
            return []

        try:
            root = ET.fromstring(xml_text)
        except Exception:
            return []

        ns = {"atom": "http://www.w3.org/2005/Atom"}

        out: List[Paper] = []
        for entry in root.findall("atom:entry", ns):
            title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
            summary = (entry.findtext("atom:summary", default="", namespaces=ns) or "").strip()
            published = (entry.findtext("atom:published", default="", namespaces=ns) or "").strip()

            if not title:
                continue

            year_int = self._year_from_published(published)
            out.append({"title": title, "summary": summary, "year": year_int})

        return out

    @staticmethod
    def _year_from_published(published: str) -> int:
        if not published:
            return 2024
        try:
            dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
            return int(dt.year)
        except Exception:
            return 2024
