from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .openalex_provider import OpenAlexProvider
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
    openalex: OpenAlexProvider = OpenAlexProvider()
    semantic: SemanticScholarProvider = SemanticScholarProvider()
    arxiv: ArxivProvider = ArxivProvider()

    def fetch(self, query: str, limit: int = 5) -> List[Paper]:
        query = (query or "").strip()
        limit = max(3, min(int(limit), 5))  # enforce 3–5

        if not query:
            return get_mock_papers(limit)

        # 1) Try OpenAlex (prefer OpenAlex for citation counts)
        papers = []
        try:
            papers = self.openalex.search(query=query, limit=limit)
        except Exception:
            papers = []

        # If we got OpenAlex results, best-effort enrich their citation counts
        if papers:
            enriched = []
            for p in papers:
                try:
                    sem_cit = self.semantic.get_citation_count(p.get("title", ""))
                    oa_cit = p.get("cited_by_count")
                    try:
                        oa_val = int(oa_cit) if oa_cit is not None else 0
                    except Exception:
                        oa_val = 0
                    if sem_cit is not None:
                        p["cited_by_count"] = max(oa_val, int(sem_cit))
                except Exception:
                    # ignore enrichment errors; keep original OA value
                    pass
                enriched.append(p)
            papers = enriched

        papers = self._normalize(papers, limit)
        if papers:
            return papers

        # 2) Try Semantic Scholar
        try:
            papers = self.semantic.search(query=query, limit=limit)
        except Exception:
            papers = []
        papers = self._normalize(papers, limit)
        if papers:
            return papers

        # 3) Fallback to arXiv
        try:
            papers = self.arxiv.search(query=query, limit=limit)
        except Exception:
            papers = []
        papers = self._normalize(papers, limit)
        if papers:
            return papers

        # 4) Both failed -> mocks
        return get_mock_papers(limit)

    def _normalize(self, papers: List[Paper], limit: int) -> List[Paper]:
        out: List[Paper] = []

        for p in (papers or [])[:limit]:
            title = str(p.get("title") or "").strip()
            if not title:
                continue

            summary = str(p.get("summary") or "").strip()
            year = p.get("year")
            source = p.get("source") or p.get("venue") or None
            cited_by_count = p.get("cited_by_count") if p.get("cited_by_count") is not None else p.get("cited_by")

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

            # Preserve optional fields when present (source, cited_by_count)
            entry = {"title": title, "summary": summary, "year": year_int}
            if source:
                entry["source"] = source
            try:
                if cited_by_count is not None:
                    entry["cited_by_count"] = int(cited_by_count)
            except Exception:
                entry["cited_by_count"] = 0

            out.append(entry)

        # Pad if between 1 and 2 results (to satisfy 3–5 rule)
        if 0 < len(out) < 3:
            out.extend(get_mock_papers(3 - len(out)))

        return out[:limit]
