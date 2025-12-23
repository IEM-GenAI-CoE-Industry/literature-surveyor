import re


def parse_topics(text: str):
    lines = text.splitlines()
    topics = []

    for line in lines:
        match = re.match(r"\s*\d+[\).\s-]+(.+)", line)
        if match:
            topics.append(match.group(1).strip())

    return topics
