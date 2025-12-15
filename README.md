# Unattended Agent Benchmark
A living sandbox for agents that must stay awake, reason over time, and decide when to act—or do nothing—as the world keeps moving. We pair a lean simulation core with pluggable scenarios to stress planning, event-driven replanning, resource awareness, and multi-objective performance.

## Why This Exists
- Modern LLM agents ace episodic tests but stumble in open-ended, unattended settings.
- Real deployments need continuity: events arrive late, resources drain, deadlines shift, and idling can be the right move.
- We measure behavior over time, not just one-shot success/failure.

## How It Works
- Simulation State: shared world state via `SimulationStateProvider`.
- Engine: advances environment, actions, events, and objectives each tick.
- Actions: long/short-running state changes.
- Events: time-bounded perturbations that force replanning.
- Objectives: success/failure checks over evolving state.
- System Prompt: scenario-specific constraints, tools, and guidance.
- Scenarios: bundle environment, events, objectives, and prompts; can be stochastic, repetitive, or one-shot.

## Scenario Principles (Ablations)
- State Monitoring & Event-Driven Replanning (sense of self, idle mode).
- Constrained Resource-Aware Action Selection (planning under scarcity).
- Time-Sensitive Prioritization of Competing Demands (which fire to fight first).
- Long-Horizon Planning Under Deadlines (clock-aware behavior).
- Multi-Objective Operational Performance (run “forever” with many metrics).

## Metrics We Track
- Environment-specific metrics aggregated into Performance Over Time (POT).
- Event Resolution Time (ERT) and Event Resolution Sequence (ERS).
- Objectives Achievement (OA) for deadline-driven tasks.
- Multi-objective scores with catastrophic-failure penalties when assets are lost.

## Example Domain: Farm World (WIP)
- Goals: keep moisture/nitrogen/battery healthy, manage ripeness, suppress pests.
- Failures: zeroed resources destroy assets; POT is scaled by failures.
- Events: surprise low-resources, pest or fire outbreaks, weather shifts.
- Signals: ERT, ERS, Event Handling Score, POT.

## Quickstart
```bash
git submodule update --init --recursive
uv pip install -e .
```

Run a toy scenario (Python 3.10+ and uv installed):
```bash
uv run python scripts/simple_scenario.py
```

Chat harness:
```bash
uv run python -m scripts.simple_chat
```

## Repository Map
- core/: simulation primitives (state provider, engine, actions, events, objectives, prompts).
- scripts/: examples (simple_scenario.py, simple_chat.py).
- meta-agents-research-environments/: upstream dependency (submodule).

## Contributing
- Keep edits ASCII unless the file already uses Unicode.
- Ruff handles formatting/import sorting; VS Code on-save formatting is wired via .vscode/settings.json.
- PR ideas: new scenario templates, metrics, or domain archetypes (Agriculture, Manufacturing, Defense).
