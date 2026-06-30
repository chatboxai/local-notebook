import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "packages"))

from workers.tasks import _build_workflow_dependency_graph


def _item(step_id, order_index, depends_on=None):
    return {
        "id": f"feature_{step_id}",
        "order_index": order_index,
        "step_id": step_id,
        "depends_on": depends_on or [],
        "step_name": step_id,
        "feature_type": "text_section",
    }


class WorkflowDependencyGraphTests(unittest.TestCase):
    def test_builds_remaining_deps_and_ordered_dependents(self):
        by_step_id, remaining_deps, dependents = _build_workflow_dependency_graph([
            _item("intro", 0),
            _item("appendix", 3, ["intro"]),
            _item("details", 1, ["intro"]),
            _item("summary", 2, ["details", "appendix"]),
        ])

        self.assertEqual(set(by_step_id.keys()), {"intro", "details", "summary", "appendix"})
        self.assertEqual(remaining_deps["intro"], set())
        self.assertEqual(remaining_deps["summary"], {"details", "appendix"})
        self.assertEqual(dependents["intro"], ["details", "appendix"])

    def test_rejects_unknown_dependency(self):
        with self.assertRaisesRegex(RuntimeError, "unknown step_id"):
            _build_workflow_dependency_graph([
                _item("intro", 0, ["missing"]),
            ])

    def test_rejects_dependency_cycle(self):
        with self.assertRaisesRegex(RuntimeError, "dependency cycle"):
            _build_workflow_dependency_graph([
                _item("a", 0, ["b"]),
                _item("b", 1, ["a"]),
            ])


if __name__ == "__main__":
    unittest.main()
