from __future__ import annotations

TEXT_BATCH_SIZE = 10


def split_into_batches(total: int, batch_size: int = TEXT_BATCH_SIZE) -> list[int]:
    if total < 1 or batch_size < 1:
        raise ValueError("Total and batch size must be greater than zero")
    full_batches, remainder = divmod(total, batch_size)
    return [batch_size] * full_batches + ([remainder] if remainder else [])


def render_master_prompt(template: str, *, count: int, keywords: str) -> str:
    required = ("{{COUNT}}", "{{KEYWORDS}}")
    missing = [placeholder for placeholder in required if placeholder not in template]
    if missing:
        raise ValueError(
            "Prompt file is missing placeholders: " + ", ".join(missing)
        )
    return template.replace("{{COUNT}}", str(count)).replace("{{KEYWORDS}}", keywords)
