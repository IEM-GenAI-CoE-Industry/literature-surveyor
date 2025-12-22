from __future__ import annotations

import os
from typing import Dict, List
import requests

Paper = Dict[str, object]  # {"title": str, "summary": str, "year": int}

class SemanticScholarProvider:
    """
    Semantic Scholar Graph API (free):
      GET https://api.semanticscholar.org/graph/v1/paper/search
        ?query=...
        &limit=...
        &fields=title,abstract,year,venue

    Restrictions satisfied:
      - No citation counts (not requested)
      - No heavy dedup
      - No PDF downloads
    """
    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
    FIELDS = "title,abstract,year,venue"

    def __init__(self, timeout_s: int = 10) -> None:
        self.timeout_s = timeout_s

    def search(self, query: str, limit: int = 5) -> List[Paper]:
        query = (query or "").strip()
        if not query:
            return []

        limit = max(1, min(int(limit), 5))

        headers = {"User-Agent": "literature-surveyor/phase4"}
        api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        if api_key:
            headers["x-api-key"] = api_key

        params = {"query": query, "limit": limit, "fields": self.FIELDS}

        try:
            resp = requests.get(self.BASE_URL, params=params, headers=headers, timeout=self.timeout_s)
            resp.raise_for_status()
            payload = resp.json()
        except Exception:
            return []

        out: List[Paper] = []
        for item in (payload.get("data") or []):
            title = (item.get("title") or "").strip()
            abstract = (item.get("abstract") or "").strip()
            year = item.get("year")

            if not title:
                continue

            summary = abstract if abstract else ""  # service will fallback if empty

            try:
                year_int = int(year) if year is not None else 2024
            except Exception:
                year_int = 2024

            out.append({"title": title, "summary": summary, "year": year_int})

        return out
