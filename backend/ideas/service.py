import re
from util.llm_factory import get_llm
from .prompt import build_prompt

class IdeaService:
    REQUIRED_COUNT = 5

    def generate(self, domain: str, venues: list[str], papers: list[dict]) -> dict:
        ideas: list[str] = []
        warning: str | None = None

        try:
            llm = get_llm()
            prompt = build_prompt(domain, venues, papers)
            raw = llm.invoke(prompt)

            text = raw.content if hasattr(raw, "content") else str(raw)
            ideas = self._parse(text)

        except Exception:
            ideas = []
            warning = "⚠️ Failed to generate ideas from the LLM. Please try again."

        if len(ideas) < self.REQUIRED_COUNT:
            warning = (
                warning or
                f"⚠️ Only {len(ideas)} idea(s) generated. Try refining your input or improving literature quality."
            )

        return {
            "ideas": ideas[:self.REQUIRED_COUNT],
            "count": len(ideas[:self.REQUIRED_COUNT]),
            "required": self.REQUIRED_COUNT,
            "warning": warning
        }

    def _parse(self, text: str) -> list[str]:
        lines = text.splitlines()
        ideas = []

        for line in lines:
            line = re.sub(r"^\d+[\).\s]+", "", line).strip()
            if len(line) > 15:
                ideas.append(line)

        return ideas