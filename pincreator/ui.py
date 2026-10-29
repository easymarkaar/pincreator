from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .config import Settings
from .pipeline import run_pipeline


class PinCreatorApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("PinCreator")
        self.geometry("790x700")
        self.minsize(720, 650)
        self.settings = Settings.load()
        self.csv_path = tk.StringVar()
        self.status = tk.StringVar(value="Ready")
        self.progress = tk.DoubleVar(value=0)
        self.entries: dict[str, ttk.Entry | ttk.Combobox] = {}
        self._build()

    def _build(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=16, pady=16)
        run_tab = ttk.Frame(notebook, padding=18)
        settings_tab = ttk.Frame(notebook, padding=18)
        notebook.add(run_tab, text="Run")
        notebook.add(settings_tab, text="Settings")

        ttk.Label(run_tab, text="Input CSV", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        picker = ttk.Frame(run_tab)
        picker.pack(fill="x", pady=(10, 22))
        ttk.Entry(picker, textvariable=self.csv_path).pack(side="left", fill="x", expand=True)
        ttk.Button(picker, text="Browse…", command=self._pick_csv).pack(side="left", padx=(8, 0))
        ttk.Label(
            run_tab,
            text="Required columns: count, keywords, prompt_file",
            foreground="#555555",
        ).pack(anchor="w")
        self.run_button = ttk.Button(run_tab, text="Start", command=self._start)
        self.run_button.pack(anchor="w", pady=22)
        ttk.Progressbar(run_tab, variable=self.progress, maximum=100).pack(fill="x")
        ttk.Label(run_tab, textvariable=self.status, wraplength=650).pack(anchor="w", pady=(10, 0))

        groups = [
            (
                "OpenAI — тексты",
                [
                    ("openai_api_key", "API key", True, "Один ключ используется и для текста, и для картинок."),
                    ("text_model", "Текстовая модель", False, "Рекомендуется gpt-5.4-mini."),
                ],
            ),
            (
                "OpenAI — изображения",
                [
                    ("image_model", "Модель изображений", False, "GPT Image 2; качество жёстко установлено на LOW для экономии."),
                ],
            ),
            (
                "ImageKit",
                [
                    ("imagekit_private_key", "Private key", True, "Приватный ключ из Developer options в ImageKit."),
                    ("imagekit_url_endpoint", "URL endpoint", False, "Например: https://ik.imagekit.io/your_imagekit_id"),
                    ("imagekit_folder", "Папка в медиатеке", False, "Необязательно. Куда складывать файлы внутри ImageKit."),
                ],
            ),
            (
                "Результаты",
                [
                    ("output_dir", "Локальная папка", False, "Здесь появятся tasks.csv, result.csv и изображения."),
                ],
            ),
        ]
        settings_tab.columnconfigure(0, weight=1)
        for group_row, (title, fields) in enumerate(groups):
            frame = ttk.LabelFrame(settings_tab, text=title, padding=(14, 10))
            frame.grid(row=group_row, column=0, sticky="ew", pady=(0, 12))
            frame.columnconfigure(1, weight=1)
            for row, (name, label, secret, hint) in enumerate(fields):
                ttk.Label(frame, text=label).grid(row=row * 2, column=0, sticky="w", pady=(4, 0))
                if name == "text_model":
                    entry = ttk.Combobox(
                        frame,
                        width=53,
                        values=("gpt-5.4-mini", "gpt-5.4", "gpt-5.4-nano"),
                    )
                elif name == "image_model":
                    entry = ttk.Combobox(
                        frame,
                        width=53,
                        values=("gpt-image-2",),
                        state="readonly",
                    )
                else:
                    entry = ttk.Entry(frame, width=55, show="•" if secret else "")
                value = str(getattr(self.settings, name))
                if isinstance(entry, ttk.Combobox):
                    entry.set(value)
                else:
                    entry.insert(0, value)
                entry.grid(row=row * 2, column=1, sticky="ew", padx=(14, 0), pady=(4, 0))
                ttk.Label(frame, text=hint, foreground="#666666").grid(
                    row=row * 2 + 1, column=1, sticky="w", padx=(14, 0), pady=(0, 4)
                )
                self.entries[name] = entry
        ttk.Button(settings_tab, text="Сохранить настройки", command=self._save_settings).grid(
            row=len(groups), column=0, sticky="e", pady=(4, 0)
        )

    def _pick_csv(self) -> None:
        selected = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if selected:
            self.csv_path.set(selected)

    def _settings_from_form(self) -> Settings:
        return Settings(
            openai_api_key=self.entries["openai_api_key"].get().strip(),
            text_model=self.entries["text_model"].get().strip(),
            image_model=self.entries["image_model"].get().strip(),
            imagekit_private_key=self.entries["imagekit_private_key"].get().strip(),
            imagekit_url_endpoint=self.entries["imagekit_url_endpoint"].get().strip(),
            imagekit_folder=self.entries["imagekit_folder"].get().strip(),
            output_dir=self.entries["output_dir"].get().strip(),
        )

    def _save_settings(self) -> None:
        try:
            self.settings = self._settings_from_form()
            self.settings.save()
        except Exception as exc:
            messagebox.showerror("Settings error", str(exc))
            return
        messagebox.showinfo("PinCreator", "Settings saved to .env")

    def _start(self) -> None:
        path = Path(self.csv_path.get())
        if not path.is_file():
            messagebox.showerror("Input error", "Choose an existing CSV file")
            return
        try:
            self.settings = self._settings_from_form()
            self.settings.save()
            self.settings.validate()
        except Exception as exc:
            messagebox.showerror("Settings error", str(exc))
            return
        self.run_button.configure(state="disabled")
        self.progress.set(0)
        threading.Thread(target=self._worker, args=(path,), daemon=True).start()

    def _worker(self, path: Path) -> None:
        try:
            result = run_pipeline(path, self.settings, self._report)
        except Exception as exc:
            self.after(0, self._failed, str(exc))
            return
        self.after(0, self._finished, result)

    def _report(self, text: str, current: int, total: int) -> None:
        percent = (current / total * 100) if total else 0
        self.after(0, lambda: (self.status.set(f"{text} — {current}/{total}"), self.progress.set(percent)))

    def _failed(self, error: str) -> None:
        self.run_button.configure(state="normal")
        self.status.set("Stopped with an error")
        messagebox.showerror("PinCreator error", error)

    def _finished(self, result: Path) -> None:
        self.run_button.configure(state="normal")
        self.progress.set(100)
        self.status.set(f"Done: {result}")
        messagebox.showinfo("PinCreator", f"Done!\n{result}")


def main() -> None:
    PinCreatorApp().mainloop()

