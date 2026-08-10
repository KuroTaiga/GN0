from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from vln_eval_results import (
    result_from_external_payload,
    result_from_gn0_log_dir,
    result_from_native_adapter_run,
    result_from_replay_summary,
    summarize_results,
)
from vln_model_registry import load_model_matrix


class VLNEvaluationResultsTest(unittest.TestCase):
    def test_result_from_replay_summary_uses_registry_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            matrix_path = _write_matrix(root)
            summary_path = root / "run" / "summary.json"
            summary_path.parent.mkdir()
            summary_path.write_text(
                json.dumps(
                    {
                        "episode_count": 2,
                        "success_count": 2,
                        "total_missions": 3,
                        "total_events": 7,
                        "mean_mission_success_rate": 1.0,
                        "mean_completion_rate": 0.5,
                    }
                ),
                encoding="utf-8",
            )
            records = load_model_matrix(matrix_path)
            record = next(row for row in records if row.model == "human_eval_json_policies")

            result = result_from_replay_summary(
                summary_path,
                record,
                mission_source="/tmp/navdp_examples",
                split="pilot",
            )

            self.assertEqual(result.model, "human_eval_json_policies")
            self.assertEqual(result.run_mode, "json_policy_replay")
            self.assertEqual(result.runner_status, "completed")
            self.assertEqual(result.episode_count, 2)
            self.assertEqual(result.total_missions, 3)
            self.assertEqual(result.mean_mission_success_rate, 1.0)
            self.assertIn('"total_events":7', result.metrics_json)

    def test_external_payload_row_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            records = load_model_matrix(_write_matrix(Path(tmpdir)))
            record = next(row for row in records if row.model == "BlockedModel")

            result = result_from_external_payload(
                {
                    "run_mode": "external_reported",
                    "runner_status": "external_reported",
                    "mission_source": "paper",
                    "split": "R2R-CE",
                    "sensor_inputs": "rgb",
                    "hardware": "paper",
                    "episode_count": 10,
                    "total_missions": 10,
                    "success_count": 6,
                    "mean_mission_success_rate": 0.6,
                    "metrics": {"spl": 0.42},
                    "notes": "paper table",
                },
                record,
            )
            summary = summarize_results([result])

            self.assertEqual(result.model, "BlockedModel")
            self.assertEqual(result.bucket, "new_post_2025")
            self.assertEqual(result.run_mode, "external_reported")
            self.assertEqual(result.mean_mission_success_rate, 0.6)
            self.assertIn('"spl":0.42', result.metrics_json)
            self.assertEqual(summary["result_count"], 1)
            self.assertEqual(summary["external_reported_count"], 1)
            self.assertEqual(summary["best_mean_mission_success_rate"], 0.6)

    def test_gn0_log_dir_row_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            records = load_model_matrix(_write_matrix(root))
            record = next(row for row in records if row.model == "GN-BAE")
            log_dir = root / "native" / "log"
            log_dir.mkdir(parents=True)
            (log_dir / "ep1.json").write_text(
                json.dumps(
                    {
                        "id": "ep1",
                        "success": 1.0,
                        "oracle_success": 1.0,
                        "spl": 0.5,
                        "path_length": 4.0,
                        "distance_to_goal": 0.2,
                    }
                ),
                encoding="utf-8",
            )
            (log_dir / "ep2.json").write_text(
                json.dumps(
                    {
                        "id": "ep2",
                        "success": 0.0,
                        "oracle_success": 1.0,
                        "spl": 0.0,
                        "path_length": 8.0,
                        "distance_to_goal": 1.5,
                    }
                ),
                encoding="utf-8",
            )

            result = result_from_gn0_log_dir(
                log_dir,
                record,
                mission_source="GN_Bench",
                split="val",
                run_mode="native_gn0_bae",
            )
            summary = summarize_results([result])

            self.assertEqual(result.model, "GN-BAE")
            self.assertEqual(result.run_mode, "native_gn0_bae")
            self.assertEqual(result.episode_count, 2)
            self.assertEqual(result.total_missions, 2)
            self.assertEqual(result.success_count, 1)
            self.assertEqual(result.mean_mission_success_rate, 0.5)
            self.assertIn('"mean_spl":0.25', result.metrics_json)
            self.assertEqual(summary["native_result_count"], 1)

    def test_native_adapter_run_row_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            records = load_model_matrix(_write_matrix(root))
            record = next(row for row in records if row.model == "FutureNav")
            run_result = SimpleNamespace(
                result_path=root / "native_adapter",
                summary_path=None,
                metrics={
                    "episode_count": 4,
                    "total_missions": 5,
                    "total_events": 12,
                    "success_count": 3,
                    "mean_mission_success_rate": 0.75,
                    "mean_completion_rate": 0.8,
                    "spl": 0.33,
                },
            )

            result = result_from_native_adapter_run(
                run_result,
                record,
                mission_source="/tmp/navdp_examples",
                split="pilot",
            )
            summary = summarize_results([result])

            self.assertEqual(result.model, "FutureNav")
            self.assertEqual(result.run_mode, "native_adapter")
            self.assertEqual(result.runner_status, "completed")
            self.assertEqual(result.episode_count, 4)
            self.assertEqual(result.total_missions, 5)
            self.assertEqual(result.total_events, 12)
            self.assertEqual(result.success_count, 3)
            self.assertEqual(result.mean_mission_success_rate, 0.75)
            self.assertEqual(result.mean_completion_rate, 0.8)
            self.assertIn('"spl":0.33', result.metrics_json)
            self.assertEqual(summary["native_result_count"], 1)


def _write_matrix(root: Path) -> Path:
    matrix_path = root / "matrix.tsv"
    matrix_path.write_text(
        "\n".join(
            [
                "model\tbucket\tsource_date\tpriority\tcheckpoint_status\tofficial_checkpoint_source\tlocal_target\tlocal_status\tnotes",
                "human_eval_json_policies\tcurrent_human_eval_baselines\t2026-07-01\tP0\tNO_CHECKPOINT_NEEDED\tlocal\tn/a\tREADY_CODE_ONLY\tpolicies",
                "GN-BAE\tcurrent_gn0_reference\t2026-06-02\tP0\tPUBLIC_READY\thf://bae\tmodel_zoo/bae\tMISSING\tbae",
                "FutureNav\tnew_post_2025\t2026-06-29\tP1\tPUBLIC_READY\thf://future\tmodel_zoo/futurenav\tFETCH_REQUIRED\tready",
                "BlockedModel\tnew_post_2025\t2026-01-01\tP2\tNO_PUBLIC_CHECKPOINT_FOUND\thttps://example.test\tmodel_zoo/blocked\tBLOCKED\tblocked",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return matrix_path


if __name__ == "__main__":
    unittest.main()
