from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from prepare_vln_checkpoints import build_checkpoint_plan, summarize_checkpoint_plan
from vln_model_registry import load_model_matrix


class PrepareVLNCheckpointsTest(unittest.TestCase):
    def test_builds_checkpoint_fetch_plan_without_downloading(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            ready = root / "bae"
            ready.mkdir()
            matrix_path = root / "matrix.tsv"
            matrix_path.write_text(
                "\n".join(
                    [
                        "model\tbucket\tsource_date\tpriority\tcheckpoint_status\tofficial_checkpoint_source\tlocal_target\tlocal_status\tnotes",
                        f"GN-BAE\tcurrent_gn0_reference\t2026-06-02\tP0\tPUBLIC_READY\thf://bae\t{ready}\tREADY\tbae",
                        "FutureNav\tnew_post_2025\t2026-06-29\tP1\tPUBLIC_READY\thf://future\tmodel_zoo/futurenav\tFETCH_REQUIRED\tready",
                        "human_eval_json_policies\tcurrent_human_eval_baselines\t2026-07-01\tP0\tNO_CHECKPOINT_NEEDED\tlocal\tn/a\tREADY_CODE_ONLY\tpolicies",
                        "BlockedModel\tnew_post_2025\t2026-01-01\tP2\tNO_PUBLIC_CHECKPOINT_FOUND\thttps://example.test\tmodel_zoo/blocked\tBLOCKED\tblocked",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            rows = build_checkpoint_plan(load_model_matrix(matrix_path))
            by_model = {row.model: row for row in rows}

            self.assertTrue(by_model["GN-BAE"].checkpoint_ready)
            self.assertTrue(by_model["GN-BAE"].fetch_supported)
            self.assertIn("TeleEmbodied/GN-BAE", by_model["GN-BAE"].command)

            self.assertFalse(by_model["FutureNav"].checkpoint_ready)
            self.assertTrue(by_model["FutureNav"].fetch_supported)
            self.assertIn("llxs/FutureNav", by_model["FutureNav"].command)
            self.assertIn("FutureNav-4B-Base/*", by_model["FutureNav"].command)

            self.assertTrue(by_model["human_eval_json_policies"].checkpoint_ready)
            self.assertFalse(by_model["human_eval_json_policies"].fetch_supported)

            self.assertFalse(by_model["BlockedModel"].fetch_supported)
            self.assertIn("blocked", by_model["BlockedModel"].blocker)

            summary = summarize_checkpoint_plan(rows)
            self.assertEqual(summary["plan_count"], 4)
            self.assertEqual(summary["checkpoint_ready_count"], 2)
            self.assertEqual(summary["fetch_supported_count"], 2)
            self.assertEqual(summary["missing_fetchable_count"], 1)


if __name__ == "__main__":
    unittest.main()
