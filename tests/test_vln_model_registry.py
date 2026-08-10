from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from vln_model_registry import filter_records, load_model_matrix, summarize_records


class VLNModelRegistryTest(unittest.TestCase):
    def test_load_filter_and_summarize_model_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_path = Path(tmpdir) / "matrix.tsv"
            matrix_path.write_text(
                "\n".join(
                    [
                        "model\tbucket\tsource_date\tpriority\tcheckpoint_status\tofficial_checkpoint_source\tlocal_target\tlocal_status\tnotes",
                        "FutureNav\tnew_post_2025\t2026-06-29\tP1\tPUBLIC_READY\thf://future\tmodel_zoo/futurenav\tFETCH_REQUIRED\tready",
                        "ReflectVLN\tnew_post_2025\t2026-07-14\tP1\tCODE_PUBLIC_CHECKPOINT_UNKNOWN\thttps://example.test\tmodel_zoo/reflectvln\tSOURCE_CHECK_REQUIRED\tcheck",
                        "VLN_Cache\tnew_post_2025\t2026-04-29\tP2\tNO_CHECKPOINT_NEEDED_ACCELERATOR\tn/a\tn/a\tRESEARCH_ONLY\taccelerator",
                        "BlockedModel\tnew_post_2025\t2026-01-01\tP2\tNO_PUBLIC_CHECKPOINT_FOUND\thttps://example.test\tmodel_zoo/blocked\tBLOCKED\tblocked",
                        "CMA\tlegacy_comparator\tpre_2026\tP0\tCHECKPOINT_REQUIRED\tlocal\tdata/checkpoints/cma.pth\tMISSING\tlegacy",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            records = load_model_matrix(matrix_path)
            runnable = filter_records(records, bucket="new_post_2025", native_runnable=True)
            source_check = filter_records(records, needs_source_check=True)
            blocked = filter_records(records, blocked=True)
            summary = summarize_records(records)

            self.assertEqual([record.model for record in runnable], ["FutureNav"])
            self.assertEqual(
                [record.model for record in source_check],
                ["CMA", "ReflectVLN"],
            )
            self.assertEqual([record.model for record in blocked], ["BlockedModel"])
            self.assertEqual(summary["model_count"], 5)
            self.assertEqual(summary["new_candidate_count"], 4)
            self.assertEqual(summary["native_runnable_count"], 1)
            self.assertEqual(summary["accelerator_count"], 1)
            self.assertEqual(summary["new_candidate_source_date_invalid_count"], 0)

    def test_new_candidate_source_date_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_path = Path(tmpdir) / "matrix.tsv"
            matrix_path.write_text(
                "\n".join(
                    [
                        "model\tbucket\tsource_date\tpriority\tcheckpoint_status\tofficial_checkpoint_source\tlocal_target\tlocal_status\tnotes",
                        "TooOld\tnew_post_2025\t2025-12-31\tP1\tPUBLIC_READY\thf://old\tmodel_zoo/old\tFETCH_REQUIRED\told",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "predates 2026-01-01 cutoff"):
                load_model_matrix(matrix_path)

            records = load_model_matrix(matrix_path, validate=False)
            summary = summarize_records(records)
            self.assertEqual(summary["new_candidate_source_date_invalid_count"], 1)


if __name__ == "__main__":
    unittest.main()
