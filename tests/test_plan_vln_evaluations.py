from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from plan_vln_evaluations import build_evaluation_plan, summarize_plan
from vln_model_registry import load_model_matrix


class VLNEvaluationPlanTest(unittest.TestCase):
    def test_builds_checkpoint_gated_evaluation_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_path = Path(tmpdir) / "matrix.tsv"
            matrix_path.write_text(
                "\n".join(
                    [
                        "model\tbucket\tsource_date\tpriority\tcheckpoint_status\tofficial_checkpoint_source\tlocal_target\tlocal_status\tnotes",
                        "GN-BAE\tcurrent_gn0_reference\t2026-06-02\tP0\tPUBLIC_READY\thf://bae\tmodel_zoo/bae\tMISSING\tbae",
                        "human_eval_json_policies\tcurrent_human_eval_baselines\t2026-07-01\tP0\tNO_CHECKPOINT_NEEDED\tlocal\tn/a\tREADY_CODE_ONLY\tpolicies",
                        "FutureNav\tnew_post_2025\t2026-06-29\tP1\tPUBLIC_READY\thf://future\tmodel_zoo/futurenav\tFETCH_REQUIRED\tready",
                        "BlockedModel\tnew_post_2025\t2026-01-01\tP2\tNO_PUBLIC_CHECKPOINT_FOUND\thttps://example.test\tmodel_zoo/blocked\tBLOCKED\tblocked",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            records = load_model_matrix(matrix_path)
            plan = build_evaluation_plan(
                records,
                mission_source="/tmp/navdp_examples",
                result_root="/tmp/results",
            )
            by_model = {row.model: row for row in plan}

            self.assertTrue(by_model["human_eval_json_policies"].ready_to_run)
            self.assertEqual(
                by_model["human_eval_json_policies"].run_mode,
                "json_policy_replay",
            )
            self.assertIn(
                "run_vln_native_eval.py",
                by_model["human_eval_json_policies"].command,
            )

            self.assertFalse(by_model["GN-BAE"].ready_to_run)
            self.assertEqual(by_model["GN-BAE"].run_mode, "native_gn0_bae")
            self.assertIn("missing local checkpoint", by_model["GN-BAE"].blocker)

            self.assertFalse(by_model["FutureNav"].ready_to_run)
            self.assertEqual(by_model["FutureNav"].adapter_status, "adapter_required")
            self.assertIn("adapter implementation status is stub", by_model["FutureNav"].blocker)

            self.assertEqual(by_model["BlockedModel"].run_mode, "external_reported")
            self.assertEqual(by_model["BlockedModel"].adapter_status, "blocked_by_checkpoint")

            summary = summarize_plan(plan)
            self.assertEqual(summary["plan_count"], 4)
            self.assertEqual(summary["ready_to_run_count"], 1)
            self.assertEqual(summary["adapter_required_count"], 1)
            self.assertEqual(summary["external_reported_count"], 1)


if __name__ == "__main__":
    unittest.main()
