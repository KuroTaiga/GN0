from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from vln_adapter_registry import assess_adapter, summarize_readiness
from vln_model_registry import load_model_matrix


class VLNAdapterRegistryTest(unittest.TestCase):
    def test_assesses_replay_native_and_adapter_required_models(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            checkpoint = root / "bae"
            checkpoint.mkdir()
            matrix_path = root / "matrix.tsv"
            matrix_path.write_text(
                "\n".join(
                    [
                        "model\tbucket\tsource_date\tpriority\tcheckpoint_status\tofficial_checkpoint_source\tlocal_target\tlocal_status\tnotes",
                        "human_eval_json_policies\tcurrent_human_eval_baselines\t2026-07-01\tP0\tNO_CHECKPOINT_NEEDED\tlocal\tn/a\tREADY_CODE_ONLY\tpolicies",
                        f"GN-BAE\tcurrent_gn0_reference\t2026-06-02\tP0\tPUBLIC_READY\thf://bae\t{checkpoint}\tREADY\tbae",
                        "FutureNav\tnew_post_2025\t2026-06-29\tP1\tPUBLIC_READY\thf://future\tmodel_zoo/futurenav\tFETCH_REQUIRED\tready",
                        "BlockedModel\tnew_post_2025\t2026-01-01\tP2\tNO_PUBLIC_CHECKPOINT_FOUND\thttps://example.test\tmodel_zoo/blocked\tBLOCKED\tblocked",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            records = load_model_matrix(matrix_path)
            readiness = {
                row.model: assess_adapter(row, mission_source="/tmp/navdp", result_path=root / row.model)
                for row in records
            }

            self.assertTrue(readiness["human_eval_json_policies"].ready_to_run)
            self.assertEqual(readiness["human_eval_json_policies"].run_mode, "json_policy_replay")
            self.assertIn("run_vln_native_eval.py", readiness["human_eval_json_policies"].command)

            self.assertTrue(readiness["GN-BAE"].ready_to_run)
            self.assertEqual(readiness["GN-BAE"].adapter_status, "existing_gn0_runner")

            self.assertFalse(readiness["FutureNav"].ready_to_run)
            self.assertEqual(readiness["FutureNav"].adapter_status, "adapter_required")
            self.assertEqual(readiness["FutureNav"].adapter_implementation_status, "stub")
            self.assertIn("adapter implementation status is stub", readiness["FutureNav"].blocker)

            self.assertEqual(readiness["BlockedModel"].run_mode, "external_reported")
            self.assertEqual(readiness["BlockedModel"].adapter_status, "blocked_by_checkpoint")

            summary = summarize_readiness(readiness.values())
            self.assertEqual(summary["adapter_count"], 4)
            self.assertEqual(summary["ready_to_run_count"], 2)
            self.assertEqual(summary["adapter_required_count"], 1)
            self.assertEqual(summary["adapter_stub_count"], 1)
            self.assertEqual(summary["external_reported_count"], 1)

    def test_check_imports_distinguishes_stub_from_missing_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            matrix_path = root / "matrix.tsv"
            matrix_path.write_text(
                "\n".join(
                    [
                        "model\tbucket\tsource_date\tpriority\tcheckpoint_status\tofficial_checkpoint_source\tlocal_target\tlocal_status\tnotes",
                        "FutureNav\tnew_post_2025\t2026-06-29\tP1\tPUBLIC_READY\thf://future\tmodel_zoo/futurenav\tFETCH_REQUIRED\tready",
                        "UnknownNative\tnew_post_2025\t2026-06-29\tP1\tPUBLIC_READY\thf://unknown\tmodel_zoo/unknown\tFETCH_REQUIRED\tunknown",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            records = load_model_matrix(matrix_path)
            readiness = {
                row.model: assess_adapter(
                    row,
                    mission_source="/tmp/navdp",
                    result_path=root / row.model,
                    check_imports=True,
                )
                for row in records
            }

            self.assertTrue(readiness["FutureNav"].adapter_importable)
            self.assertEqual(
                readiness["FutureNav"].adapter_implementation_status,
                "stub",
            )
            self.assertFalse(readiness["FutureNav"].ready_to_run)

            self.assertFalse(readiness["UnknownNative"].adapter_importable)
            self.assertEqual(
                readiness["UnknownNative"].adapter_implementation_status,
                "missing",
            )
            self.assertIn("missing adapter implementation", readiness["UnknownNative"].blocker)


if __name__ == "__main__":
    unittest.main()
