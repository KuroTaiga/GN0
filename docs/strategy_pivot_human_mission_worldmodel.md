# GN0 Strategy Pivot: Human Missions And World-Model Simulation

Date: 2026-08-05

## Purpose

This note records the current strategic decision after comparing GN0 with more
visible sim-to-real work such as Sudo, and after reviewing the Aug 5 research
notes in:

- `/Users/dongjk/Downloads/机器人Agent.pdf`
- `/Users/dongjk/Downloads/世界模型 _ VLA.pdf`

The recommendation is to keep GN0/NavDP as the core, but change the public
thesis and split execution into two tracks:

1. A near-term flagship benchmark/product story around human-centric mission
   navigation.
2. A parallel R&D track that connects 3DGS simulation with the agent, world
   model, and VLA trend through object-level 3DGS manipulation and fast
   rendering.

## Diagnosis

GN0's current public framing is technically correct but too infrastructure-like:
generation, evaluation, and policy learning for VLN in 3DGS scenes. That reads
as a research stack.

The stronger external story is:

> Given a scanned real indoor space, GN0 generates human-centric missions,
> evaluates task and social success, and supports robot deployment with no
> per-scene real training.

The current local work already points in this direction. NavDP contains a
substantial human-centric mission-stream benchmark design, generated examples,
social-law scaffolding, mission-family variants, and BEV visualizations. GN0's
evaluation side is the weaker link: the human evaluator, RL task, and social
metrics are still mostly placeholders. That should determine the immediate work.

## Track A: Human-Centric Mission Navigation

This is the main 2-4 week execution track.

### Positioning

Do not lead with "3DGS VLN benchmark." Lead with:

> Human-centric sim-to-real navigation in scanned spaces.

The claim should be about robots completing useful human-facing tasks, not just
following instructions:

- deliver to the correct person;
- navigate while respecting social constraints;
- serve people in a queue or mission stream;
- recover from human motion, wrong-person distractors, and blocked paths.

### First Flagship Scope

Lead with three mission families only:

- `deliver_to_human`
- `navigate_with_social_constraints`
- `serve_queue`

Defer the broader ten-family story, dense multi-robot cases, async mode, and RL
until the evaluator is real and the demos are clean.

### Required Technical Work

Finish deterministic replay and metrics before training or RL:

- `correct_human_reached`
- `object_delivered`
- `deadline_success`
- `wrong_human_contact`
- `minimum_human_robot_distance`
- `personal_space_violation_duration`
- `queue_order_violation`
- per-mission success/failure traces

Then expose the same metrics as:

- benchmark report fields;
- baseline comparison tables;
- reward components for later RL;
- failure signatures for an agentic debugging loop.

### Demo Package

Produce demos that are legible to non-benchmark readers:

- side-by-side baseline vs human-aware route;
- uncut BEV rollout with task/social metrics overlaid;
- first-person or 3DGS-rendered frames when available;
- one real-space scanned scene if a robot demo is feasible.

The current BEV images are useful but still look like internal debug plots.
Before public release they need cleaner labels, fewer raw IDs, and explicit
success/failure annotations.

### Near-Term Success Bar

A credible first release is:

- 5 scenes;
- 3 mission families;
- 5 variants per family;
- deterministic evaluator;
- 3-5 baselines;
- public examples and reproducer;
- one clear video showing a socially aware policy beating a shortest-path or
  no-human-awareness baseline.

## Track B: 3DGS Object Manipulation For Agent + World Model + VLA

This is the parallel R&D track. It should not block Track A.

### Why This Track Matters

The world-model/VLA trend is moving toward learned simulators, action-conditioned
video prediction, compact latent planning, and agentic closed-loop improvement.
GN0's current gap is that its 3DGS scenes are visually strong but mostly static.
To connect with the trend, GN0 needs editable 3D worlds:

> Scan a real scene, move or insert objects/humans in the 3DGS scene, render the
> counterfactual quickly, and use the result for task generation, policy
> evaluation, world-model supervision, or VLA planning traces.

This is where "manipulate 3DGS object in scene with fast rendering" becomes the
technical bridge.

### Research Signals From The Aug 5 Notes

The agent PDF highlights several system patterns worth adopting:

- ASPIRE: trace-rich robot execution engine, failure diagnosis, skill library,
  and evolutionary search. The useful lesson for GN0 is to log primitive-level
  evidence and convert failures into reusable navigation/social-recovery skills.
- TiPToP: modular perception, planning, and execution can beat end-to-end VLA on
  structured manipulation while remaining explainable. The useful lesson is not
  "ignore VLA"; it is to wrap VLA/world-model components inside an interpretable
  simulator/planner stack.
- ENPIRE and harness-engineering notes: self-improvement works when there is a
  repeatable environment API, automatic reset, objective reward, rollout logs,
  and auditable artifacts. GN0 should make the evaluator and trace format the
  stable harness interface.

The world-model/VLA PDF points to these relevant directions:

- DINO-style latent world models: patch-level visual features preserve spatial
  detail better than global embeddings for planning. This is relevant to VLN:
  predict spatial consequences in latent feature maps before trying full video.
- SC3-Eval: self-consistent forward/inverse dynamics and cross-view consistency
  can turn video models into policy evaluators, but compute is heavy. Use this
  as a research reference, not the first implementation target.
- CompACT: extreme token compression suggests a practical way to plan in compact
  latent states rather than photorealistic pixels.
- DreamDojo: human videos plus latent actions plus distillation can produce a
  real-time robot world model. The lesson is that speed may require distillation
  and causal rollout, not a heavy diffusion model in the control loop.
- GS-World: the field is explicitly moving toward engine-driven generative
  simulation with differentiable rendering, physics tokens, object/articulation
  priors, and VLA training loops.
- ManualVLA: the most directly relevant 3DGS example uses object-level 3DGS
  assets for LEGO/object rearrangement, iteratively places objects, renders
  subgoal images, and generates intermediate supervision without manual labels.

### GN0 Opportunity

GN0 can own a narrower, more realistic version of GS-World:

> A 3DGS-native counterfactual scene engine for human-centric navigation and
> object rearrangement in scanned indoor spaces.

This does not require solving full physics or full video generation at first.
The first useful layer is object-level rigid transforms with reliable rendering
and evaluator-visible state.

### Technical MVP

Build an `ObjectGS` layer on top of existing scene 3DGS:

1. Object extraction and registry
   - assign Gaussian subsets to object IDs using segmentation masks, scene
     annotations, or manual seeds;
   - store object pose, bounding box, semantic label, affordance tags, and
     collision proxy;
   - keep static scene Gaussians separate from dynamic object Gaussians.

2. Fast transform rendering
   - transform object Gaussian means and covariances at render time;
   - avoid retraining the full scene for each object move;
   - composite static scene splats with dynamic object splats;
   - cache static background/tile bins where possible;
   - support multi-view rendering for BEV, egocentric, and third-person traces.

3. Geometry and physics proxy
   - use splats for visual rendering;
   - use mesh, convex hull, cylinder, or oriented bounding box proxies for
     collision, reachability, and social metrics;
   - start with rigid objects and human avatars only;
   - defer soft bodies, articulated furniture, contact-rich manipulation, and
     differentiable physics.

4. Counterfactual task generator
   - object move, insert, remove, distractor, and blocked-path variants;
   - automatic labels: target pose, visibility, occlusion, collision risk,
     route change, social-law violation;
   - generated subgoal images and text traces for planning/VLA supervision.

5. World-model/VLA bridge
   - do not train a giant video model first;
   - start with DINO/V-JEPA feature rollouts over rendered frames;
   - compare compact latent dynamics against direct metric evaluator outcomes;
   - use object state tokens and affordance tokens as intermediate supervision;
   - expose trace packets: observation, object state, action/subgoal, rendered
     next state, evaluator outcome.

### First Experiments

The R&D track should answer four questions in order:

1. Can we move one segmented 3DGS object in a scanned scene and render from
   multiple views without visible artifacts?
2. Can we generate task-relevant counterfactuals quickly enough for dataset
   generation, not necessarily real-time control?
3. Can object-state proxies make the evaluator agree with rendered outcomes?
4. Can a compact latent model predict enough about route feasibility, visibility,
   or collision/social violation to improve planning?

### Do Not Overclaim

This track has real risk:

- object segmentation in 3DGS scenes may be noisy;
- splat geometry and collision geometry can disagree;
- occlusion and hole filling are hard after object removal;
- contact physics is not solved by 3DGS rendering;
- fast rendering is easier than accurate physical simulation;
- full action-conditioned video world models are compute-heavy.

The first public claim should therefore be "counterfactual 3DGS scene rendering
for embodied navigation and mission supervision," not "full generative physics
world model."

## Harness Architecture: GN0 As An Interactive World Runtime

The right system shape is to mimic the modern agent harness, but specialize it
for VLN, VLA, and world-model interaction:

> planner proposes high-level actions -> grounder checks whether those actions
> are possible -> simulator executes low-level effects -> evaluator returns
> traces, failures, and rewards -> planner/model revises.

This makes GN0 more than a dataset generator. It becomes an interactive world
runtime with a stable API for agents, navigation models, VLA executors, and
latent world models.

### Core Interfaces

Define the environment around a small set of stable calls:

- `Reset(scene_id, episode_id, seed)`
- `Observe(agent_id, view_spec)`
- `ListSkills(agent_id)`
- `CheckAffordance(skill_call, world_state)`
- `Step(skill_call)`
- `Render(camera_spec)`
- `Evaluate(trace_id)`
- `Replay(trace_id, range)`

The skill/action API should be explicit before training learned grounders:

- `NavigateTo(target_region | target_object | target_human)`
- `FollowHuman(human_id)`
- `Wait(duration | condition)`
- `DeliverToHuman(object_id, human_id)`
- `ServeNextInQueue(queue_id)`
- `YieldToHuman(human_id | flow_id)`
- `MoveObject3DGS(object_id, pose_delta | target_pose)`
- `RenderView(camera_id | pose)`

These are the allowed verbs the agent can plan with. Each verb needs matching
preconditions, affordance checks, simulator effects, evaluator events, and
failure signatures.

### C++ Runtime Decision

Use C++ for the runtime core where speed and determinism matter:

- 3DGS rendering and dynamic object compositing;
- collision and distance queries;
- human/avatar state updates;
- deterministic episode replay;
- evaluator metric accumulation;
- trace packet serialization;
- rollout batching for benchmark generation.

Keep Python for research flexibility:

- VLN/VLA model adapters;
- DINO/V-JEPA feature extraction experiments;
- plotting, reports, and notebooks;
- quick benchmark orchestration;
- training loops until the interfaces settle.

The practical architecture is:

- C++ world server/runtime library;
- Python bindings or a local RPC layer for model code;
- structured trace files shared by both sides;
- command-line replay and validation tools;
- optional web/demo viewer later.

Do not rewrite everything in C++ immediately. Start by moving only the hot loop
and stable contracts into C++ while keeping the experimental model layer thin
and replaceable.

### Runtime Components

1. `gn0_world_core`
   - scene state, agents, humans, objects, mission state, random seed, clock;
   - pure state transition logic with deterministic replay.

2. `gn0_affordance`
   - preset checks for geometry, social distance, queue order, deadlines,
     object ownership, visibility, and route validity;
   - later learned success predictors attached behind the same interface.

3. `gn0_render`
   - static 3DGS scene renderer;
   - dynamic object/human Gaussian subset transform and compositing;
   - multi-view output for egocentric, BEV, third-person, and dataset traces.

4. `gn0_eval`
   - task success metrics;
   - social violation metrics;
   - failure signatures;
   - reward components for later RL or agent search.

5. `gn0_harness`
   - planner/model adapter;
   - skill-call validation;
   - rollout loop;
   - trace logging;
   - automatic replay and scoring.

### Trace Contract

The trace should be treated as the main product artifact. Each step should log:

- scene and episode IDs;
- world-state summary;
- observation references;
- planner prompt or model input hash;
- proposed skill call;
- affordance result;
- simulator state delta;
- rendered frame references;
- evaluator events;
- success, reward, and failure reason.

This gives GN0 the same advantage modern coding agents gained from harnesses:
the model is no longer trusted blindly. Every action is checked against an
external world state, replayed, scored, and turned into useful failure evidence.

### C++ Milestones

1. Define schemas first
   - skill-call schema;
   - world-state schema;
   - trace schema;
   - evaluator event schema.

2. Build a minimal C++ replay/evaluator core
   - load one generated mission episode;
   - replay robot/human/object states;
   - compute deterministic metrics;
   - emit JSONL traces.

3. Add Python bindings or local RPC
   - call `Reset`, `Step`, `Observe`, and `Evaluate` from Python;
   - run existing baseline policies through the C++ core.

4. Add fast dynamic 3DGS rendering
   - static scene cache;
   - transformed object Gaussian subsets;
   - evaluator-visible object proxies.

5. Attach model adapters
   - VLN planner proposes skill calls;
   - VLA executor handles low-level action chunks where useful;
   - world model predicts future latent/affordance state for planning support.

## Combined Roadmap

### Week 1

- Finish `deliver_to_human` adapter normalization and deterministic metrics.
- Add focused tests for correct human, wrong human, deadline, and personal-space
  behavior.
- Freeze the first skill-call, world-state, evaluator-event, and trace schemas.
- Define the C++/Python boundary for the runtime core.
- Write a one-page public positioning draft for Human-Centric GN-Bench.

### Weeks 2-3

- Add `navigate_with_social_constraints` and `serve_queue` metrics.
- Scaffold the minimal C++ replay/evaluator core and call it from Python.
- Run existing baseline policies through the same trace/evaluator contract.
- Produce clean baseline-vs-aware BEV videos.
- Package a 5-scene pilot split.
- Prototype object registry format for 3DGS scene objects.

### Weeks 4-6

- Build first object-transform renderer prototype:
  static scene + 1-3 movable rigid object Gaussian subsets.
- Generate counterfactual object placement examples with evaluator-visible
  collision/visibility labels.
- Add trace packets compatible with harness-style agent debugging and future
  world-model training.

### Weeks 6-10

- Add DINO/V-JEPA feature extraction over rendered traces.
- Train or test a small latent transition baseline for route feasibility,
  visibility, or object-state prediction.
- Compare pure evaluator, object-token model, and rendered-latent model as
  planning aids.

## Decision

Primary direction: finish and publicize the human-centric mission navigation
benchmark.

Secondary direction: develop object-level 3DGS manipulation as the bridge from
GN0's simulation gap to agent + world model + VLA trends.

Execution architecture: build GN0 as an interactive harness runtime. The hot
loop should move toward C++ for rendering, replay, collision, evaluator metrics,
and batched rollouts. Python should remain the model-adapter and research layer
until the contracts stabilize.

The two tracks reinforce each other. Track A gives GN0 a near-term visible proof
and evaluator. Track B turns GN0 from a static 3DGS VLN benchmark into an
editable counterfactual world engine that can produce traces for agents, world
models, and VLA systems.
