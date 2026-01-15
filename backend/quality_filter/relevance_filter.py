from typing import List, Dict
import logging
logger = logging.getLogger(__name__)


KEYWORDS = [
    "llm",
    "language model",
    "transformer",
    "nlp",
    "gpt",
    "attention",
    "generative"
]


def _count_keyword_hits(text: str) -> int:
    text = text.lower()
    return sum(1 for kw in KEYWORDS if kw in text)


def filter_venues(domain: str, venues: List[Dict]) -> List[Dict]:
    filtered = []

    for venue in venues:
        combined_text = f"{venue.get('name', '')} {venue.get('description', '')}"
        score = _count_keyword_hits(combined_text)

        if score >= 1:
            venue["relevance_score"] = score
            filtered.append(venue)

    return filtered


def filter_papers(domain: str, papers: List[Dict], max_papers: int = 5) -> List[Dict]:
    scored = []

    for paper in papers:
        combined_text = f"{paper.get('title', '')} {paper.get('abstract', '')}"
        score = _count_keyword_hits(combined_text)

        if score >= 2:
            paper["relevance_score"] = score
            scored.append(paper)

    # sort by relevance
    scored.sort(key=lambda x: x["relevance_score"], reverse=True)

    return scored[:max_papers]


def quality_filter(domain: str, venues: List[Dict], papers: List[Dict]) -> Dict:
    return {
        "filtered_venues": filter_venues(domain, venues),
        "filtered_papers": filter_papers(domain, papers),
    }

def filter_by_domain(domain, venues, papers):
    logger.info("QUALITY FILTER RUNNING")
    logger.info("Domain: %s", domain)
    logger.info("Venues before filtering: %d", len(venues))
    logger.info("Papers before filtering: %d", len(papers))