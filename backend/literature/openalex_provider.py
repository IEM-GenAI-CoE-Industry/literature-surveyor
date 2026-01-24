import os
from typing import List, Dict
import requests
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load backend .env if present (for EMAIL param)
env_path = Path(__file__).resolve().parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

Paper = Dict[str, object]


class OpenAlexProvider:
    """Simple OpenAlex /works provider used for literature retrieval.

    Returns a list of paper dicts with keys: title, summary, year, source, cited_by_count
    """
    BASE = "https://api.openalex.org/works"

    def __init__(self, timeout_s: int = 10) -> None:
        self.timeout_s = timeout_s

    def search(self, query: str, limit: int = 5) -> List[Paper]:
        q = (query or "").strip()
        if not q:
            return []

        per_page = max(1, min(int(limit), 5))
        params = {"search": q, "per_page": per_page, "sort": "cited_by_count:desc"}

        email = os.getenv("EMAIL")
        if email:
            params["mailto"] = email

        try:
            resp = requests.get(self.BASE, params=params, timeout=self.timeout_s)
            resp.raise_for_status()
            payload = resp.json()
        except Exception as e:
            logger.debug("OpenAlex search failed: %s", e)
            return []

        out: List[Paper] = []
        for item in (payload.get("results") or []):
            title = (item.get("display_name") or "").strip()

            # OpenAlex may provide an abstract string or an inverted index
            abstract = item.get("abstract")
            if not abstract:
                inv = item.get("abstract_inverted_index") or {}
                if inv:
                    # Reconstruct roughly (join tokens) — keep short
                    try:
                        # abstract_inverted_index is {token: [positions]}
                        tokens = sorted(inv.items(), key=lambda x: x[1][0] if x[1] else 0)
                        abstract = " ".join(t[0] for t in tokens)[:1000]
                    except Exception:
                        abstract = ""

            # Year fallback
            year = item.get("publication_year") or item.get("publication_date")
            try:
                year_int = int(year) if year is not None else None
            except Exception:
                year_int = None

            primary_loc = item.get("primary_location") or {}
            source = (primary_loc.get("source") or {}).get("display_name") if primary_loc else None

            cited = item.get("cited_by_count", 0)
            try:
                cited_val = int(cited or 0)
            except Exception:
                cited_val = 0

            if not title:
                continue

            out.append({
                "title": title,
                "summary": abstract or "",
                "year": year_int,
                "source": source or "OpenAlex",
                "cited_by_count": cited_val,
            })

        return out
