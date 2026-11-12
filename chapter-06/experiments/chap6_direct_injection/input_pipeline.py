from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class StructuredInput:
    task: str
    domain: str
    primary_input: str
    aux_data_refs: List[str]
    tone_preferences: str | None
    extra_instructions: str | None


class InputValidationError(Exception):
    pass


def parse_to_structured(user_prompt: str) -> StructuredInput:
    """Very simple structured parser.

    In a real system this would parse JSON/form fields. Here we implement a
    deterministic toy mapping so that the experiment is self-contained.

    Rules:
    - If the prompt mentions "support" -> domain="support"; similarly for
      hr/legal/engineering; otherwise "general".
    - task is inferred from keywords: summarize, classify, answer, transform.
    - extra_instructions is the full user prompt (for attack carriage).
    """

    lowered = user_prompt.lower()

    if "support" in lowered:
        domain = "support"
    elif "hr" in lowered:
        domain = "hr"
    elif "legal" in lowered:
        domain = "legal"
    elif "engineer" in lowered or "bug" in lowered:
        domain = "engineering"
    else:
        domain = "general"

    if "summarize" in lowered or "summary" in lowered:
        task = "summarize"
    elif "classify" in lowered or "category" in lowered:
        task = "classify"
    elif "translate" in lowered or "rewrite" in lowered or "paraphrase" in lowered:
        task = "transform_text"
    else:
        task = "answer_question"

    primary_input = user_prompt
    aux_data_refs: List[str] = []
    tone_preferences: str | None = None
    extra_instructions: str | None = user_prompt

    return StructuredInput(
        task=task,
        domain=domain,
        primary_input=primary_input,
        aux_data_refs=aux_data_refs,
        tone_preferences=tone_preferences,
        extra_instructions=extra_instructions,
    )


def sanitize_structured(inp: StructuredInput) -> tuple[StructuredInput, List[str]]:
    """Apply simple sanitization to reduce direct prompt injection risk.

    - Strip common override tokens from extra_instructions.
    - Replace tool-abuse phrases with neutral placeholders.
    """

    actions: List[str] = []
    extra = inp.extra_instructions or ""
    lowered = extra.lower()

    replacements = {
        "ignore previous instructions": "[removed override]",
        "ignore the previous instructions": "[removed override]",
        "disregard earlier instructions": "[removed override]",
        "act as dan": "[removed persona override]",
        "jailbreak": "[removed jailbreak]",
        "reveal your system prompt": "[removed system prompt leak]",
        "show me the system prompt": "[removed system prompt leak]",
        "print the system prompt": "[removed system prompt leak]",
        "download all hr files": "[removed bulk download request]",
        "exfiltrate data": "[removed data exfiltration request]",
        "delete all logs": "[removed log deletion request]",
        "run rm -rf": "[removed destructive command]",
        "export all salaries": "[removed salary export request]",
    }

    for needle, replacement in replacements.items():
        if needle in lowered:
            actions.append(f"sanitize:{needle}")
            # simple case-insensitive replacement by rebuilding string
            extra = _case_insensitive_replace(extra, needle, replacement)
            lowered = extra.lower()

    sanitized = StructuredInput(
        task=inp.task,
        domain=inp.domain,
        primary_input=inp.primary_input,
        aux_data_refs=inp.aux_data_refs,
        tone_preferences=inp.tone_preferences,
        extra_instructions=extra,
    )
    return sanitized, actions


def _case_insensitive_replace(text: str, sub: str, repl: str) -> str:
    """Replace all case-insensitive occurrences of `sub` with `repl`.

    Implemented without regex to keep dependencies minimal.
    """

    result_chars: List[str] = []
    i = 0
    n = len(text)
    sub_l = sub.lower()
    m = len(sub_l)
    while i < n:
        if i + m <= n and text[i : i + m].lower() == sub_l:
            result_chars.append(repl)
            i += m
        else:
            result_chars.append(text[i])
            i += 1
    return "".join(result_chars)
