from __future__ import annotations

import re
from typing import Any

CPF_PATTERN = re.compile(r"(?<!\d)\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?!\d)")
ACCOUNT_PATTERN = re.compile(
    r"\b(?P<label>ag[eê]ncia|conta|cpf)\s*[:\-]?\s*(?P<value>[\d.\-/]+)",
    re.IGNORECASE,
)
ADDRESS_PATTERN = re.compile(
    r"\b(rua|avenida|av\.|travessa|alameda|rodovia)\s+[^,\n]+(?:,\s*\d+)?",
    re.IGNORECASE,
)


def mask_sensitive_text(value: str) -> str:
    masked = CPF_PATTERN.sub("***.***.***-**", value)
    masked = ACCOUNT_PATTERN.sub(lambda match: f"{match.group('label')}: <mascarado>", masked)
    return ADDRESS_PATTERN.sub("<endereco mascarado>", masked)


def mask_sensitive_value(value: Any) -> Any:
    if isinstance(value, str):
        return mask_sensitive_text(value)
    if isinstance(value, dict):
        return {key: mask_sensitive_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [mask_sensitive_value(item) for item in value]
    return value
