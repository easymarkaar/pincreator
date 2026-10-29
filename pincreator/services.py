from __future__ import annotations

import base64
from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import requests
from openai import OpenAI

from .csv_io import PinTask


TASK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "pins": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "image_prompt": {"type": "string"},
                },
                "required": ["title", "description", "image_prompt"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["pins"],
    "additionalProperties": False,
}


class OpenAIService:
    def __init__(self, api_key: str, text_model: str, image_model: str) -> None:
        self.client = OpenAI(api_key=api_key)
        self.text_model = text_model
        self.image_model = image_model

    def create_tasks(
        self,
        *,
        master_prompt: str,
        count: int,
        start_index: int,
        batch_number: int,
        total_batches: int,
        total_requested: int,
        previous_titles: list[str],
    ) -> list[PinTask]:
        schema = deepcopy(TASK_SCHEMA)
        pins_schema = schema["properties"]["pins"]
        pins_schema["minItems"] = count
        pins_schema["maxItems"] = count
        previous = "\n".join(f"- {title}" for title in previous_titles) or "None yet"
        response = self.client.responses.create(
            model=self.text_model,
            instructions=(
                "Follow the user's master prompt exactly. Return exactly the requested number "
                "of unique Pinterest records in the required structured format."
            ),
            input=(
                f"{master_prompt}\n\n"
                "Batch context added by PinCreator:\n"
                f"- Total records requested: {total_requested}\n"
                f"- Current batch: {batch_number} of {total_batches}\n"
                f"- Records to create in this batch: {count}\n"
                "- Do not repeat these titles from earlier batches:\n"
                f"{previous}"
            ),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "pin_tasks",
                    "strict": True,
                    "schema": schema,
                }
            },
        )
        data = json.loads(response.output_text)
        pins = data["pins"]
        if len(pins) != count:
            raise RuntimeError(f"Model returned {len(pins)} tasks instead of {count}")
        return [
            PinTask(
                id=f"pin-{start_index + offset:05d}",
                title=pin["title"].strip(),
                description=pin["description"].strip(),
                image_prompt=pin["image_prompt"].strip(),
            )
            for offset, pin in enumerate(pins)
        ]

    def create_image(self, prompt: str, destination: Path) -> None:
        result = self.client.images.generate(
            model=self.image_model,
            prompt=prompt,
            size="1024x1536",
            quality="low",
        )
        encoded = result.data[0].b64_json
        if not encoded:
            raise RuntimeError("Image model returned no image data")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(base64.b64decode(encoded))


class ImageKitService:
    upload_url = "https://upload.imagekit.io/api/v1/files/upload"

    def __init__(self, private_key: str, url_endpoint: str, folder: str) -> None:
        self.private_key = private_key
        self.url_endpoint = url_endpoint.rstrip("/")
        self.folder = folder

    def upload(self, path: Path) -> str:
        with path.open("rb") as image:
            response = requests.post(
                self.upload_url,
                auth=(self.private_key, ""),
                files={"file": (path.name, image, "image/png")},
                data={"fileName": path.name, "folder": self.folder, "useUniqueFileName": "false"},
                timeout=120,
            )
        response.raise_for_status()
        payload = response.json()
        url = payload.get("url")
        if not url and payload.get("filePath"):
            url = self.url_endpoint + "/" + str(payload["filePath"]).lstrip("/")
        if not url:
            raise RuntimeError("ImageKit response contains no URL")
        return str(url)

