import csv
import tempfile
import unittest
from pathlib import Path

from pincreator.csv_io import read_jobs, write_rows


class CsvIoTests(unittest.TestCase):
    def test_reads_relative_prompt_file(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "prompt.txt").write_text("Make a pin", encoding="utf-8")
            (root / "input.csv").write_text(
                "count,keywords,prompt_file\n2,demo topic,prompt.txt\n", encoding="utf-8"
            )
            jobs = read_jobs(root / "input.csv")
            self.assertEqual(jobs[0].count, 2)
            self.assertEqual(jobs[0].prompt_file, (root / "prompt.txt").resolve())

    def test_rejects_missing_columns(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "input.csv"
            path.write_text("count,keywords\n2,demo topic\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must contain columns"):
                read_jobs(path)

    def test_output_uses_excel_friendly_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "result.csv"
            write_rows(path, ["title"], [{"title": "Тестовый заголовок"}])
            with path.open("r", encoding="utf-8-sig", newline="") as file:
                self.assertEqual(next(csv.DictReader(file))["title"], "Тестовый заголовок")


if __name__ == "__main__":
    unittest.main()

