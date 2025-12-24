def build_prompt(domain: str, venues: list[str], papers: list[dict]) -> str:
    venue_text = ", ".join(venues)

    paper_block = "\n".join(
        f"- {p['title']} ({p['year']}): {p['summary']}"
        for p in papers
    )

    return f"""
You are an expert researcher preparing submissions to top-tier venues.

DOMAIN:
{domain}

TARGET VENUES:
{venue_text}

EXISTING CONTEXT PAPERS:
{paper_block}

TASK:
Generate EXACTLY 5 research-grade paper ideas.

STRICT CONSTRAINTS:
• Each idea must identify a specific technical problem
• Each idea must specify a methodological contribution
• Avoid vague phrases like "novel approach", "comprehensive study"
• Ideas must be experimentally or mathematically testable
• Ideas should be plausible extensions, refinements, or reframings
  of the provided literature—not summaries of them

STYLE:
• Write each idea as a paper title
• One sentence per idea
• No explanations
• No bullet commentary

OUTPUT FORMAT:
1. <idea>
2. <idea>
3. <idea>
4. <idea>
5. <idea>
"""
