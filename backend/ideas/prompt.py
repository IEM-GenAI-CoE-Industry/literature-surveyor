def build_prompt(domain, venues, papers):
    venue_text = ", ".join(venues)

    paper_text = "\n".join(
        f"- {p['title']} ({p.get('year', 'N/A')}): {p.get('summary', '')}"
        for p in papers
    )

    return f"""
You are an expert researcher in {domain}.

Target venues:
{venue_text}

Example papers:
{paper_text}

Generate 3–5 novel research topics inspired by the above papers.
Return only a numbered list.
"""
