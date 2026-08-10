"""Model-facing NavDP mission records for native VLN adapters."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
GN_BENCH_TOOLS = REPO_ROOT / "GN-Bench-Tools"
if str(GN_BENCH_TOOLS) not in sys.path:
    sys.path.insert(0, str(GN_BENCH_TOOLS))

from GN_Bench.human_eval.scenario_adapter import (  # noqa: E402
    HumanCentricEpisode,
    NavDPScenarioAdapter,
)


JsonDict = dict[str, Any]


@dataclass(frozen=True)
class VLNAdapterMissionInput:
    episode_id: str
    scenario_path: str
    scene_id: str
    raw_scene_id: str
    dataset: str
    schema_version: str
    mission_id: str
    mission_type: str
    instruction: str
    instruction_sources: JsonDict
    assigned_robot_ids: list[str]
    robot_start_map_pose_by_robot: JsonDict
    goal_world: list[float]
    goal_world_by_robot: JsonDict
    target_human_id: str
    target_region_id: str
    target_object_id: str
    release_time: float | None
    deadline: float | None
    priority: float | None
    social_law_ids: list[str]
    success_conditions: list[str]
    humans: list[JsonDict]
    scene_assets: JsonDict
    compact_metadata: JsonDict
    raw: JsonDict = field(default_factory=dict)

    def to_dict(self) -> JsonDict:
        return asdict(self)


def build_navdp_adapter_inputs(
    source: str | Path,
    *,
    navdp_root: str | Path | None = None,
    mission_types: Iterable[str] = (),
    limit: int = 0,
    include_raw: bool = False,
) -> list[VLNAdapterMissionInput]:
    adapter = NavDPScenarioAdapter(navdp_root=navdp_root)
    episodes = adapter.load_path(source)
    allowed = {mission_type for mission_type in mission_types if mission_type}
    records: list[VLNAdapterMissionInput] = []
    for episode in episodes:
        for mission in _mission_dicts(episode.payload):
            if allowed and str(mission.get("mission_type", "")) not in allowed:
                continue
            records.append(
                mission_to_adapter_input(
                    episode,
                    mission,
                    include_raw=include_raw,
                )
            )
            if limit > 0 and len(records) >= limit:
                return records
    return records


def mission_to_adapter_input(
    episode: HumanCentricEpisode,
    mission: JsonDict,
    *,
    include_raw: bool = False,
) -> VLNAdapterMissionInput:
    payload = episode.payload
    assigned_robot_ids = _assigned_robot_ids(payload, mission)
    robot_starts = _robot_start_map_pose_by_robot(payload, assigned_robot_ids)
    instruction_sources = _instruction_sources(mission, assigned_robot_ids)
    goal_world_by_robot = _goal_world_by_robot(mission, assigned_robot_ids)
    return VLNAdapterMissionInput(
        episode_id=str(episode.episode_id),
        scenario_path=str(episode.scenario_path),
        scene_id=str(episode.scene_id),
        raw_scene_id=str(episode.raw_scene_id),
        dataset=str(episode.dataset),
        schema_version=str(episode.schema_version),
        mission_id=str(mission.get("mission_id", "")),
        mission_type=str(mission.get("mission_type", "")),
        instruction=_primary_instruction(instruction_sources),
        instruction_sources=instruction_sources,
        assigned_robot_ids=assigned_robot_ids,
        robot_start_map_pose_by_robot=robot_starts,
        goal_world=_primary_goal(goal_world_by_robot, mission, assigned_robot_ids),
        goal_world_by_robot=goal_world_by_robot,
        target_human_id=str(mission.get("target_human_id") or ""),
        target_region_id=str(mission.get("target_region_id") or ""),
        target_object_id=str(mission.get("target_object_id") or ""),
        release_time=_optional_number(mission.get("release_time")),
        deadline=_optional_number(mission.get("deadline")),
        priority=_optional_number(mission.get("priority")),
        social_law_ids=_string_list(mission.get("social_law_ids")),
        success_conditions=_string_list(mission.get("success_conditions")),
        humans=_human_summaries(payload),
        scene_assets=dict(episode.scene_assets or {}),
        compact_metadata=_compact_metadata(mission),
        raw={"mission": mission, "scenario": payload} if include_raw else {},
    )


def summarize_adapter_inputs(records: Iterable[VLNAdapterMissionInput]) -> JsonDict:
    rows = list(records)
    return {
        "mission_input_count": len(rows),
        "episode_count": len({row.episode_id for row in rows}),
        "mission_types": sorted({row.mission_type for row in rows}),
        "missing_instruction_count": sum(1 for row in rows if not row.instruction),
        "missing_goal_count": sum(1 for row in rows if not row.goal_world),
        "multi_robot_mission_count": sum(1 for row in rows if len(row.assigned_robot_ids) > 1),
    }


def write_adapter_inputs(
    records: Iterable[VLNAdapterMissionInput],
    result_path: str | Path,
) -> tuple[Path, Path]:
    result_dir = Path(result_path)
    result_dir.mkdir(parents=True, exist_ok=True)
    rows = list(records)
    jsonl_path = result_dir / "adapter_inputs.jsonl"
    summary_path = result_dir / "summary.json"
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row.to_dict(), sort_keys=True) + "\n")
    summary_path.write_text(
        json.dumps(summarize_adapter_inputs(rows), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return jsonl_path, summary_path


def _mission_dicts(payload: JsonDict) -> list[JsonDict]:
    missions = payload.get("missions", [])
    if not isinstance(missions, list):
        return []
    return [mission for mission in missions if isinstance(mission, dict)]


def _assigned_robot_ids(payload: JsonDict, mission: JsonDict) -> list[str]:
    values: list[str] = []
    _append_string(values, mission.get("assigned_robot_id"))
    values.extend(_string_list(mission.get("assigned_robot_ids")))
    metadata = _metadata(mission)
    values.extend(_string_list(metadata.get("active_robot_ids")))
    by_robot = metadata.get("planned_goal_world_by_robot")
    if isinstance(by_robot, dict):
        values.extend(str(robot_id) for robot_id in by_robot.keys())
    for event in _event_dicts(payload):
        if str(event.get("mission_id", "")) != str(mission.get("mission_id", "")):
            continue
        if event.get("event_type") not in {"robot_assignment", "mission_assignment"}:
            continue
        _append_string(values, event.get("robot_id"))
        values.extend(_string_list(event.get("robot_ids")))
    if not values:
        values.extend(_robot_ids(payload))
    return _dedupe(values)


def _robot_start_map_pose_by_robot(payload: JsonDict, robot_ids: list[str]) -> JsonDict:
    allowed = set(robot_ids)
    starts: JsonDict = {}
    for robot in _robot_dicts(payload):
        robot_id = str(robot.get("robot_id") or robot.get("id") or "")
        if not robot_id or (allowed and robot_id not in allowed):
            continue
        pose = robot.get("start_map_pose")
        starts[robot_id] = dict(pose) if isinstance(pose, dict) else {}
    return starts


def _instruction_sources(mission: JsonDict, robot_ids: list[str]) -> JsonDict:
    metadata = _metadata(mission)
    sources: JsonDict = {}
    _put_text(sources, "mission.instruction", mission.get("instruction"))
    _put_text(sources, "metadata.instruction", metadata.get("instruction"))
    _put_text(sources, "metadata.coarse_instruction", metadata.get("coarse_instruction"))
    robot_instructions = metadata.get("robot_instructions")
    if isinstance(robot_instructions, dict):
        for robot_id in robot_ids:
            _put_text(
                sources,
                f"metadata.robot_instructions.{robot_id}",
                robot_instructions.get(robot_id),
            )
    for index, entry in enumerate(_instruction_entries(mission, metadata)):
        _put_text(sources, f"mission_instructions.{index}", entry.get("instruction"))
    return sources


def _instruction_entries(mission: JsonDict, metadata: JsonDict) -> list[JsonDict]:
    entries: list[JsonDict] = []
    for source in (mission.get("mission_instructions"), metadata.get("mission_instructions")):
        if isinstance(source, list):
            entries.extend(entry for entry in source if isinstance(entry, dict))
    return entries


def _primary_instruction(sources: JsonDict) -> str:
    for key in sorted(sources):
        if key.startswith("metadata.robot_instructions."):
            return str(sources[key])
    for key in (
        "metadata.instruction",
        "mission.instruction",
        "metadata.coarse_instruction",
        "mission_instructions.0",
    ):
        value = sources.get(key)
        if value:
            return str(value)
    return ""


def _goal_world_by_robot(mission: JsonDict, robot_ids: list[str]) -> JsonDict:
    metadata = _metadata(mission)
    by_robot = metadata.get("planned_goal_world_by_robot")
    if isinstance(by_robot, dict):
        return {
            str(robot_id): _number_list(value)
            for robot_id, value in by_robot.items()
            if _number_list(value)
        }
    goal = _number_list(metadata.get("planned_goal_world"))
    if not goal:
        goal = _number_list(metadata.get("target_human_world"))
    if not goal:
        return {}
    target_robot_ids = robot_ids or [str(mission.get("assigned_robot_id") or "")]
    return {robot_id: goal for robot_id in target_robot_ids if robot_id}


def _primary_goal(
    goal_world_by_robot: JsonDict,
    mission: JsonDict,
    robot_ids: list[str],
) -> list[float]:
    for robot_id in robot_ids:
        value = goal_world_by_robot.get(robot_id)
        if isinstance(value, list) and value:
            return value
    for value in goal_world_by_robot.values():
        if isinstance(value, list) and value:
            return value
    metadata = _metadata(mission)
    return _number_list(metadata.get("planned_goal_world"))


def _human_summaries(payload: JsonDict) -> list[JsonDict]:
    summaries: list[JsonDict] = []
    for human in _human_dicts(payload):
        human_id = str(human.get("human_id") or human.get("id") or "")
        if not human_id:
            continue
        summaries.append(
            {
                "human_id": human_id,
                "role": str(human.get("role") or ""),
                "resource_id": str(human.get("resource_id") or ""),
                "start_map_pose": dict(human.get("start_map_pose") or {}),
                "trajectory_sample_count": _trajectory_sample_count(human),
            }
        )
    return summaries


def _compact_metadata(mission: JsonDict) -> JsonDict:
    metadata = _metadata(mission)
    keys = (
        "contact_distance_m",
        "mission_end_time_s",
        "target_human_world",
        "planned_goal_world",
        "planned_goal_world_by_robot",
        "endpoint_semantics",
        "avoidance_semantics",
        "mission_description",
    )
    return {key: metadata[key] for key in keys if key in metadata}


def _metadata(mission: JsonDict) -> JsonDict:
    metadata = mission.get("metadata", {})
    return metadata if isinstance(metadata, dict) else {}


def _event_dicts(payload: JsonDict) -> list[JsonDict]:
    event_log = payload.get("event_log", [])
    if isinstance(event_log, dict):
        event_log = event_log.get("events", [])
    if not isinstance(event_log, list):
        return []
    return [event for event in event_log if isinstance(event, dict)]


def _robot_dicts(payload: JsonDict) -> list[JsonDict]:
    robots = payload.get("robots", [])
    if not isinstance(robots, list):
        return []
    return [robot for robot in robots if isinstance(robot, dict)]


def _human_dicts(payload: JsonDict) -> list[JsonDict]:
    humans = payload.get("humans", [])
    if not isinstance(humans, list):
        return []
    return [human for human in humans if isinstance(human, dict)]


def _robot_ids(payload: JsonDict) -> list[str]:
    return [
        str(robot.get("robot_id") or robot.get("id"))
        for robot in _robot_dicts(payload)
        if robot.get("robot_id") or robot.get("id")
    ]


def _trajectory_sample_count(human: JsonDict) -> int:
    for key in ("trajectory", "path", "planned_trajectory"):
        value = human.get(key)
        if isinstance(value, list):
            return len(value)
        if isinstance(value, dict):
            for nested_key in ("samples", "points", "poses"):
                nested_value = value.get(nested_key)
                if isinstance(nested_value, list):
                    return len(nested_value)
    return 0


def _put_text(target: JsonDict, key: str, value: Any) -> None:
    if isinstance(value, str) and value.strip():
        target[key] = value.strip()


def _append_string(values: list[str], value: Any) -> None:
    if isinstance(value, str) and value.strip():
        values.append(value.strip())


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def _number_list(value: Any) -> list[float]:
    if not isinstance(value, list):
        return []
    numbers = [_optional_number(item) for item in value]
    if any(item is None for item in numbers):
        return []
    return [float(item) for item in numbers if item is not None]


def _optional_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
