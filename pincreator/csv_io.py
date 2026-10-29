from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class InputJob:
    count: int
    keywords: str
    prompt_file: Path


@dataclass(frozen=True, slots=True)
class PinTask:
    id: str
    title: str
    description: str
    image_prompt: str


def read_jobs(path: Path) -> list[InputJob]:
    jobs: list[InputJob] = []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required = {"count", "keywords", "prompt_file"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("CSV must contain columns: count, keywords, prompt_file")
        for line, row in enumerate(reader, start=2):
            try:
                count = int(row["count"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Line {line}: count must be an integer") from exc
            if count < 1:
                raise ValueError(f"Line {line}: count must be greater than zero")
            keywords = (row["keywords"] or "").strip()
            if not keywords:
                raise ValueError(f"Line {line}: keywords cannot be empty")
            prompt_file = Path((row["prompt_file"] or "").strip())
            if not prompt_file.is_absolute():
                prompt_file = path.parent / prompt_file
            if not prompt_file.is_file():
                raise ValueError(f"Line {line}: prompt file not found: {prompt_file}")
            jobs.append(InputJob(count, keywords, prompt_file.resolve()))
    if not jobs:
        raise ValueError("CSV contains no jobs")
    return jobs


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

