from __future__ import annotations
from typing import Dict, List

Paper = Dict[str, object]  # {"title": str, "summary": str, "year": int}

_MOCK = [
    {
        "title": "Fast, Metadata-Only Literature Retrieval for LLM Context Building",
        "summary": "Presents a lightweight method to fetch a small set of papers using public metadata APIs for downstream idea generation.",
        "year": 2024,
    },
    {
        "title": "Provider Fallback Patterns for Reliable Scholarly Search",
        "summary": "Discusses timeouts, graceful degradation, and mock fallbacks to keep literature retrieval stable when upstream APIs fail.",
        "year": 2023,
    },
    {
        "title": "Using Small Paper Sets to Ground LLM-Based Research Ideation",
        "summary": "Studies how 3–5 paper summaries can improve LLM ideation quality without heavy retrieval or PDF downloads.",
        "year": 2024,
    },
    {
        "title": "Minimal Deduplication for Small Retrieval Pipelines",
        "summary": "Explores simple heuristics for reducing near-duplicate results while keeping logic minimal and low-cost.",
        "year": 2022,
    },
    {
        "title": "Survey Prototyping with Preprint Metadata",
        "summary": "Shows how arXiv metadata and abstracts can support rapid survey prototypes without full-text access.",
        "year": 2021,
    },
]

def get_mock_papers(limit: int = 5) -> List[Paper]:
    limit = max(3, min(int(limit), 5))  # enforce 3–5
    return _MOCK[:limit]
