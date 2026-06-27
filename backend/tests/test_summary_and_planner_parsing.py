import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "packages"))

from services import summary_service
from services.workflow_planner import _parse_json_object


class SummaryRetryTests(unittest.IsolatedAsyncioTestCase):
    async def test_file_summary_retries_empty_and_invalid_responses(self):
        calls = []
        responses = [
            "",
            "not json",
            '{"summary": "Recovered summary", "keywords": ["Agentic Engineering"]}',
        ]

        async def fake_llm_complete(*args, **kwargs):
            calls.append(args[0])
            return responses.pop(0)

        original_llm_complete = summary_service._llm_complete
        original_retry_delay = summary_service.SUMMARY_RETRY_BASE_DELAY
        summary_service._llm_complete = fake_llm_complete
        summary_service.SUMMARY_RETRY_BASE_DELAY = 0
        try:
            result = await summary_service.generate_file_summary(
                "notes.pdf",
                ["Segment summary one.", "Segment summary two."],
                "api-key",
                "https://example.test",
                "model",
            )
        finally:
            summary_service._llm_complete = original_llm_complete
            summary_service.SUMMARY_RETRY_BASE_DELAY = original_retry_delay

        self.assertEqual(result["summary"], "Recovered summary")
        self.assertEqual(result["keywords"], ["Agentic Engineering"])
        self.assertEqual(len(calls), 3)
        self.assertIn("Previous response was invalid", calls[1])


class PlannerParsingTests(unittest.TestCase):
    def test_parse_fenced_json_with_unescaped_inner_quotes(self):
        raw = '''```json
{"steps": [{"step_id": "three_alignments", "step_name": "核心框架", "instruction": "说明为什么这三条线是成为"五倍十倍工程师"的前提。"}, {"step_id": "harness", "step_name": "Harness 编排层", "instruction": "解释 Harness 作为模型上层编排工具的角色（即"harness engine"）。"}]}
```'''

        parsed = _parse_json_object(raw, preferred_keys=("steps",))

        self.assertEqual(len(parsed["steps"]), 2)
        self.assertIn('"五倍十倍工程师"', parsed["steps"][0]["instruction"])
        self.assertIn('"harness engine"', parsed["steps"][1]["instruction"])


if __name__ == "__main__":
    unittest.main()
