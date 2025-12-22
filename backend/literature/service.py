from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .semantic_scholar import SemanticScholarProvider
from .arxiv_provider import ArxivProvider
from .mock_papers import get_mock_papers

Paper = Dict[str, object]  # {"title": str, "summary": str, "year": int}

@dataclass
class LiteratureService:
    """
    PHASE 4 — LITERATURE RETRIEVAL (LIMITED)

    Output: list of 3–5 paper dicts:
      { "title": "...", "summary": "...", "year": 202X }

    Rules:
      - No citation counts
      - No heavy deduplication
      - No PDF downloads
      - If no abstract -> summary from title
      - If providers fail -> return mock papers
    """
    semantic: SemanticScholarProvider = SemanticScholarProvider()
    arxiv: ArxivProvider = ArxivProvider()

    def fetch(self, query: str, limit: int = 5) -> List[Paper]:
        query = (query or "").strip()
        limit = max(3, min(int(limit), 5))  # enforce 3–5

        if not query:
            return get_mock_papers(limit)

        # 1) Try Semantic Scholar
        papers = self.semantic.search(query=query, limit=limit)
        papers = self._normalize(papers, limit)
        if papers:
            return papers

        # 2) Fallback to arXiv
        papers = self.arxiv.search(query=query, limit=limit)
        papers = self._normalize(papers, limit)
        if papers:
            return papers

        # 3) Both failed -> mocks
        return get_mock_papers(limit)

    def _normalize(self, papers: List[Paper], limit: int) -> List[Paper]:
        out: List[Paper] = []

        for p in (papers or [])[:limit]:
            title = str(p.get("title") or "").strip()
            if not title:
                continue

            summary = str(p.get("summary") or "").strip()
            year = p.get("year")

            try:
                year_int = int(year) if year is not None else 2024
            except Exception:
                year_int = 2024

            # If abstract missing -> title-based summary
            if not summary:
                summary = (
                    f"This work appears to focus on: {title}. "
                    f"(Abstract unavailable; summary generated from title only.)"
                )

            out.append({"title": title, "summary": summary, "year": year_int})

        # Pad if between 1 and 2 results (to satisfy 3–5 rule)
        if 0 < len(out) < 3:
            out.extend(get_mock_papers(3 - len(out)))

        return out[:limit]
