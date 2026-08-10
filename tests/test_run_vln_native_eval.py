from __future__ import annotations

import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

import run_vln_native_eval
import vln_adapter_registry
from vln_adapter_registry import VLNAdapterSpec
from vln_adapters.base import ADAPTER_STATUS_NATIVE_READY
from vln_model_registry import load_model_matrix


class RunVLNNativeEvalTest(unittest.TestCase):
    def test_python_adapter_dispatch_writes_normalized_result_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            module_path = root / "ready_adapter.py"
            module_path.write_text(
                "\n".join(
                    [
                        "from vln_adapters.base import ADAPTER_STATUS_NATIVE_READY, VLNAdapterRunResult",
                        "IMPLEMENTATION_STATUS = ADAPTER_STATUS_NATIVE_READY",
                        "class ReadyAdapter:",
                        "    IMPLEMENTATION_STATUS = ADAPTER_STATUS_NATIVE_READY",
                        "    def __init__(self, context):",
                        "        self.context = context",
                        "    def run(self):",
                        "        self.context.result_path.mkdir(parents=True, exist_ok=True)",
                        "        return VLNAdapterRunResult(",
                        "            result_path=self.context.result_path,",
                        "            metrics={",
                        "                'episode_count': 2,",
                        "                'total_missions': 3,",
                        "                'total_events': 4,",
                        "                'success_count': 1,",
                        "                'mean_mission_success_rate': 0.5,",
                        "                'mean_completion_rate': 0.75,",
                        "            },",
                        "        )",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            sys.path.insert(0, str(root))
            self.addCleanup(lambda: sys.path.remove(str(root)))
            importlib.invalidate_caches()

            checkpoint = root / "checkpoint"
            checkpoint.mkdir()
            result_path = root / "result"
            matrix_path = root / "matrix.tsv"
            matrix_path.write_text(
                "\n".join(
                    [
                        "model\tbucket\tsource_date\tpriority\tcheckpoint_status\tofficial_checkpoint_source\tlocal_target\tlocal_status\tnotes",
                        f"ReadyAdapterModel\tnew_post_2025\t2026-06-29\tP1\tPUBLIC_READY\thf://ready\t{checkpoint}\tREADY\tready",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            spec = VLNAdapterSpec(
                model="ReadyAdapterModel",
                runner="python_adapter",
                adapter_module="ready_adapter",
                adapter_class="ReadyAdapter",
                implementation_status=ADAPTER_STATUS_NATIVE_READY,
            )
            old_spec = vln_adapter_registry.ADAPTER_SPECS.get("ReadyAdapterModel")
            vln_adapter_registry.ADAPTER_SPECS["ReadyAdapterModel"] = spec
            self.addCleanup(self._restore_spec, old_spec)

            record = load_model_matrix(matrix_path)[0]
            run_vln_native_eval._run_python_adapter(
                record,
                "/tmp/navdp_examples",
                result_path,
                "pilot",
            )

            payload = json.loads((result_path / "vln_result.json").read_text())
            self.assertEqual(payload["model"], "ReadyAdapterModel")
            self.assertEqual(payload["run_mode"], "native_adapter")
            self.assertEqual(payload["runner_status"], "completed")
            self.assertEqual(payload["episode_count"], 2)
            self.assertEqual(payload["total_missions"], 3)
            self.assertEqual(payload["total_events"], 4)
            self.assertEqual(payload["success_count"], 1)
            self.assertEqual(payload["mean_mission_success_rate"], 0.5)
            self.assertEqual(payload["mean_completion_rate"], 0.75)
            self.assertIn('"episode_count":2', payload["metrics_json"])

    @staticmethod
    def _restore_spec(old_spec) -> None:
        if old_spec is None:
            vln_adapter_registry.ADAPTER_SPECS.pop("ReadyAdapterModel", None)
        else:
            vln_adapter_registry.ADAPTER_SPECS["ReadyAdapterModel"] = old_spec


if __name__ == "__main__":
    unittest.main()
