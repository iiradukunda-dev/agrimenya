"""Shared rendering helpers for grounded agricultural assistant answers."""
import re


def format_assistant_answer(answer: str) -> str:
    """Turn legacy one-line evidence explanations into readable Markdown sections."""
    labels = {
        "what the records show": "What the records show",
        "how to use it": "What it means",
        "next checks": "What to check next",
        "source": "Evidence",
    }
    marker = re.compile(r"\s*(What the records show|How to use it|Next checks|Source):\s*", re.IGNORECASE)
    matches = list(marker.finditer(answer or ""))
    if not matches or matches[0].start() > 3:
        return answer

    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(answer)
        body = answer[match.end():end].strip()
        if body:
            sections.append((labels[match.group(1).casefold()], body))
    if not sections:
        return answer

    formatted = []
    for title, body in sections:
        if title == "What to check next":
            limit = re.search(
                r"\s*(This is historical district evidence, not a farm forecast or proof of cause\.?)",
                body, re.IGNORECASE,
            )
            if limit:
                body = (body[:limit.start()] + body[limit.end():]).strip()
                formatted.append("### Evidence limits\n\n" + limit.group(1).strip())
        if body:
            formatted.append(f"### {title}\n\n{body}")
    return "\n\n".join(formatted)


def has_source_citation(answer: str) -> bool:
    text = str(answer or "").casefold()
    return "source:" in text or "### evidence" in text or "**evidence**" in text
