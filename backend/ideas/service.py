from .prompt import build_prompt
from .parser import parse_topics
from .fallback import fallback_topics


class IdeaGenerationService:
    def generate(self, *, domain, venues, papers, llm_call):
        prompt = build_prompt(
            domain=domain,
            venues=venues,
            papers=papers,
        )

        raw_output = llm_call(prompt)

        topics = parse_topics(raw_output)

        # Enforce ≥ 3 ideas
        if len(topics) < 3:
            topics = topics + fallback_topics(domain)

        return topics[:5]
