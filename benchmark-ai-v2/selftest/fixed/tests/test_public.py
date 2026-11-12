import unittest

from mlkit import data_prep, eval_metrics, llm_call, train_plan


class PublicTests(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(data_prep.normalize("  ａ\t b "), "a b")

    def test_scrub_email(self):
        self.assertEqual(data_prep.scrub_pii("mail a@b.vn nhé"), ("mail <EMAIL> nhé", 1))

    def test_grad_accum(self):
        self.assertEqual(train_plan.grad_accum(32, 8), 4)

    def test_accuracy(self):
        self.assertEqual(eval_metrics.accuracy(["a", "b"], ["a", "a"]), 0.5)

    def test_extract_fenced(self):
        self.assertEqual(llm_call.extract_json('```json\n{"a": 1}\n```'), {"a": 1})


if __name__ == "__main__":
    unittest.main()
