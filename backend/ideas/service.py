import re
from util.llm_factory import get_llm
from .prompt import build_prompt
from .fallback import fallback_ideas

class IdeaService:
    REQUIRED_COUNT = 5

    def generate(self, domain: str, venues: list[str], papers: list[dict]) -> list[str]:
        ideas: list[str] = []

        try:
            llm = get_llm()
            prompt = build_prompt(domain, venues, papers)
            raw = llm.invoke(prompt)

            text = raw.content if hasattr(raw, "content") else str(raw)
            ideas = self._parse(raw)

        except Exception:
            ideas = []

        # Enforce EXACTLY 5 ideas
        if len(ideas) < self.REQUIRED_COUNT:
            fillers = fallback_ideas(domain)
            for f in fillers:
                if len(ideas) >= self.REQUIRED_COUNT:
                    break
                ideas.append(f)

        return ideas[:self.REQUIRED_COUNT]

    def _parse(self, text: str) -> list[str]:
        lines = text.splitlines()
        ideas = []

        for line in lines:
            line = re.sub(r"^\d+[\).\s]+", "", line).strip()
            if len(line) > 15:
                ideas.append(line)

        return ideas
