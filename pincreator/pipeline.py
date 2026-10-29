from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from .config import Settings
from .csv_io import PinTask, read_jobs, write_rows
from .prompts import render_master_prompt, split_into_batches
from .services import ImageKitService, OpenAIService

Progress = Callable[[str, int, int], None]


def run_pipeline(csv_path: Path, settings: Settings, progress: Progress) -> Path:
    settings.validate()
    jobs = read_jobs(csv_path)
    total = sum(job.count for job in jobs)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(settings.output_dir) / stamp
    images_dir = run_dir / "images"
    tasks_path = run_dir / "tasks.csv"
    result_path = run_dir / "result.csv"

    openai = OpenAIService(settings.openai_api_key, settings.text_model, settings.image_model)
    imagekit = ImageKitService(
        settings.imagekit_private_key,
        settings.imagekit_url_endpoint,
        settings.imagekit_folder,
    )

    tasks: list[PinTask] = []
    next_index = 1
    progress("Creating pin tasks", 0, total)
    for job in jobs:
        template = job.prompt_file.read_text(encoding="utf-8")
        batch_sizes = split_into_batches(job.count)
        previous_titles: list[str] = []
        for batch_number, batch_size in enumerate(batch_sizes, start=1):
            master_prompt = render_master_prompt(
                template,
                count=batch_size,
                keywords=job.keywords,
            )
            batch = openai.create_tasks(
                master_prompt=master_prompt,
                count=batch_size,
                start_index=next_index,
                batch_number=batch_number,
                total_batches=len(batch_sizes),
                total_requested=job.count,
                previous_titles=previous_titles,
            )
            tasks.extend(batch)
            previous_titles.extend(task.title for task in batch)
            next_index += batch_size
            progress(
                f"Creating text batch {batch_number}/{len(batch_sizes)}",
                len(tasks),
                total,
            )

    write_rows(
        tasks_path,
        ["id", "title", "description", "image_prompt"],
        [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "image_prompt": task.image_prompt,
            }
            for task in tasks
        ],
    )

    results: list[dict[str, str]] = []
    for completed, task in enumerate(tasks, start=1):
        progress(f"Generating {task.id}", completed - 1, total)
        image_path = images_dir / f"{task.id}.png"
        openai.create_image(task.image_prompt, image_path)
        progress(f"Uploading {task.id}", completed - 1, total)
        image_url = imagekit.upload(image_path)
        results.append(
            {
                "id": task.id,
                "image_url": image_url,
                "title": task.title,
                "description": task.description,
            }
        )
        write_rows(result_path, ["id", "image_url", "title", "description"], results)
        progress("Pins completed", completed, total)
    return result_path.resolve()

