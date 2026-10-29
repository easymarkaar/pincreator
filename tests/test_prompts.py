import unittest

from pincreator.prompts import render_master_prompt, split_into_batches


class PromptTests(unittest.TestCase):
    def test_replaces_count_and_keywords(self) -> None:
        result = render_master_prompt(
            "Create {{COUNT}} pins for {{KEYWORDS}}.",
            count=100,
            keywords="demo topic, tutorial ideas",
        )
        self.assertEqual(result, "Create 100 pins for demo topic, tutorial ideas.")

    def test_requires_both_placeholders(self) -> None:
        with self.assertRaisesRegex(ValueError, "KEYWORDS"):
            render_master_prompt("Create {{COUNT}} pins.", count=5, keywords="demo topic")

    def test_splits_one_hundred_into_ten_batches(self) -> None:
        self.assertEqual(split_into_batches(100), [10] * 10)

    def test_last_batch_can_be_smaller(self) -> None:
        self.assertEqual(split_into_batches(23), [10, 10, 3])


if __name__ == "__main__":
    unittest.main()
