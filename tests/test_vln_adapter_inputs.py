from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from vln_adapters.navdp_inputs import (
    build_navdp_adapter_inputs,
    summarize_adapter_inputs,
    write_adapter_inputs,
)


class VLNAdapterInputsTest(unittest.TestCase):
    def test_builds_model_facing_navdp_mission_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest_path, scenario_path = _write_navdp_input_fixture(root)

            records = build_navdp_adapter_inputs(manifest_path, navdp_root=root)
            summary = summarize_adapter_inputs(records)

            self.assertEqual(len(records), 1)
            record = records[0]
            self.assertEqual(record.episode_id, "fixture_adapter_input")
            self.assertEqual(record.scenario_path, str(scenario_path))
            self.assertEqual(record.raw_scene_id, "demo_scene")
            self.assertEqual(record.dataset, "FixtureSet")
            self.assertEqual(record.mission_id, "mission_deliver_to_human_001")
            self.assertEqual(record.mission_type, "deliver_to_human")
            self.assertEqual(record.assigned_robot_ids, ["robot_alpha"])
            self.assertEqual(record.goal_world, [4.0, 5.0])
            self.assertEqual(record.goal_world_by_robot["robot_alpha"], [4.0, 5.0])
            self.assertEqual(record.robot_start_map_pose_by_robot["robot_alpha"]["x"], 1.0)
            self.assertEqual(record.target_human_id, "human_target")
            self.assertEqual(record.release_time, 0.0)
            self.assertEqual(record.deadline, 30.0)
            self.assertIn("Deliver to the target human", record.instruction)
            self.assertIn(
                "metadata.robot_instructions.robot_alpha",
                record.instruction_sources,
            )
            self.assertEqual(record.humans[0]["human_id"], "human_target")
            self.assertEqual(record.compact_metadata["contact_distance_m"], 0.7)

            self.assertEqual(summary["mission_input_count"], 1)
            self.assertEqual(summary["episode_count"], 1)
            self.assertEqual(summary["mission_types"], ["deliver_to_human"])
            self.assertEqual(summary["missing_instruction_count"], 0)
            self.assertEqual(summary["missing_goal_count"], 0)

    def test_filters_writes_jsonl_and_can_include_raw_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest_path, _ = _write_navdp_input_fixture(root)

            records = build_navdp_adapter_inputs(
                manifest_path,
                navdp_root=root,
                mission_types=["deliver_to_human"],
                include_raw=True,
            )
            jsonl_path, summary_path = write_adapter_inputs(records, root / "out")

            self.assertTrue(jsonl_path.exists())
            self.assertTrue(summary_path.exists())
            rows = [
                json.loads(line)
                for line in jsonl_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["raw"]["mission"]["mission_id"], "mission_deliver_to_human_001")
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["mission_input_count"], 1)


def _write_navdp_input_fixture(root: Path) -> tuple[Path, Path]:
    scenario_dir = root / "scenarios"
    scenario_dir.mkdir(parents=True)
    scenario_path = scenario_dir / "fixture_adapter_input.json"
    scenario = {
        "schema_version": "0.1",
        "scenario_id": "fixture_adapter_input",
        "scene_id": "demo_scene",
        "scene_assets": {
            "dataset": "FixtureSet",
            "scene_dir": "test_scenes/demo_scene",
        },
        "robots": [
            {
                "robot_id": "robot_alpha",
                "start_map_pose": {"x": 1.0, "y": 2.0, "yaw": 0.5},
            }
        ],
        "humans": [
            {
                "human_id": "human_target",
                "role": "target_person",
                "resource_id": "subject_001",
                "start_map_pose": {"x": 4.0, "y": 5.0, "yaw": 0.0},
                "trajectory": [{"t": 0.0}, {"t": 1.0}],
            }
        ],
        "missions": [
            {
                "mission_id": "mission_deliver_to_human_001",
                "mission_type": "deliver_to_human",
                "assigned_robot_id": "robot_alpha",
                "release_time": 0.0,
                "deadline": 30.0,
                "priority": 2,
                "target_human_id": "human_target",
                "target_object_id": "payload_generic_delivery_item",
                "target_region_id": None,
                "social_law_ids": ["personal_space_L1"],
                "success_conditions": ["correct_human_reached", "object_delivered"],
                "metadata": {
                    "instruction": "Bring the payload to the waiting person.",
                    "robot_instructions": {
                        "robot_alpha": "Deliver to the target human and stop at contact distance."
                    },
                    "planned_goal_world": [4.0, 5.0],
                    "target_human_world": [4.0, 5.0],
                    "contact_distance_m": 0.7,
                },
            }
        ],
        "event_log": [
            {
                "event_type": "robot_assignment",
                "mission_id": "mission_deliver_to_human_001",
                "robot_id": "robot_alpha",
            }
        ],
    }
    scenario_path.write_text(json.dumps(scenario), encoding="utf-8")
    manifest_path = root / "manifest.json"
    manifest_path.write_text(
        json.dumps({"examples": [{"path": "scenarios/fixture_adapter_input.json"}]}),
        encoding="utf-8",
    )
    return manifest_path, scenario_path


if __name__ == "__main__":
    unittest.main()
