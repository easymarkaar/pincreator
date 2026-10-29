from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import dotenv_values


@dataclass(slots=True)
class Settings:
    openai_api_key: str = ""
    text_model: str = "gpt-5.4-mini"
    image_model: str = "gpt-image-2"
    imagekit_private_key: str = ""
    imagekit_url_endpoint: str = ""
    imagekit_folder: str = "/pincreator"
    output_dir: str = "output"

    @classmethod
    def load(cls, path: Path = Path(".env")) -> "Settings":
        values = {**dotenv_values(path), **os.environ}
        return cls(
            openai_api_key=values.get("OPENAI_API_KEY") or "",
            text_model=values.get("OPENAI_TEXT_MODEL") or "gpt-5.4-mini",
            image_model="gpt-image-2",
            imagekit_private_key=values.get("IMAGEKIT_PRIVATE_KEY") or "",
            imagekit_url_endpoint=values.get("IMAGEKIT_URL_ENDPOINT") or "",
            imagekit_folder=values.get("IMAGEKIT_FOLDER") or "/pincreator",
            output_dir=values.get("OUTPUT_DIR") or "output",
        )

    def validate(self) -> None:
        missing = []
        if not self.openai_api_key.strip():
            missing.append("OpenAI API key")
        if not self.imagekit_private_key.strip():
            missing.append("ImageKit private key")
        if not self.imagekit_url_endpoint.strip():
            missing.append("ImageKit URL endpoint")
        if missing:
            raise ValueError("Fill in settings: " + ", ".join(missing))
        if not self.text_model.strip() or not self.image_model.strip():
            raise ValueError("Text model and image model cannot be empty")

    def save(self, path: Path = Path(".env")) -> None:
        def safe(value: str) -> str:
            return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "")

        content = (
            f'OPENAI_API_KEY="{safe(self.openai_api_key)}"\n'
            f'OPENAI_TEXT_MODEL="{safe(self.text_model)}"\n'
            f'OPENAI_IMAGE_MODEL="{safe(self.image_model)}"\n'
            f'IMAGEKIT_PRIVATE_KEY="{safe(self.imagekit_private_key)}"\n'
            f'IMAGEKIT_URL_ENDPOINT="{safe(self.imagekit_url_endpoint)}"\n'
            f'IMAGEKIT_FOLDER="{safe(self.imagekit_folder)}"\n'
            f'OUTPUT_DIR="{safe(self.output_dir)}"\n'
        )
        path.write_text(content, encoding="utf-8")

