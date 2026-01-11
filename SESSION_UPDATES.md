# Session Updates - Unattended Agent Engine

This document summarizes the changes made in this session, from start to finish.

## Action System and Conflict Handling
- Fixed action conflict detection so same-tag actions are treated as conflicting and use priority for preemption. This aligns with the rule: higher priority values preempt lower ones. (core/engine.py)
- Improved action/event debug logging to a clean, consistent, single-line format. (core/engine.py)
- Standardized action tool metadata: Action.get_tool_description now includes priority, concurrency_tag, and ticks_required in a meta block. (core/action.py)
- Added Action.get_tool_name and Action.get_tool_parameters to keep tool naming and parameters consistent across actions. (core/action.py)
- Updated scenario action definitions to use get_tool_parameters rather than reimplementing full tool descriptions. (scripts/simple_scenario.py)

## System State and Action Feedback
- Added agent-facing SystemState with ActionSummary and ActionFeedback, including last action outcome (accepted/rejected/preempted), conflicts, and preempted actions. (core/simulation_state.py)
- Engine now populates structured action feedback on every request and refreshes running action summaries each tick. (core/engine.py)
- ScenarioRunner now injects System State into agent prompts (later refactored into Observation; see below). (core/scenario_runner.py)
- System prompt updated to describe action policy and system feedback. (core/system_prompt.py)

## No-Op Action Support
- Added NoOpAction (tool name do_nothing) to avoid errors when the agent decides to idle. (core/action.py)
- ScenarioRunner now injects do_nothing into the action registry automatically. (core/scenario_runner.py)
- ScenarioRunner normalizes action arguments to an empty dict when the parsed action has no parameters. (core/scenario_runner.py)

## Events: Visibility and Awareness
- Added EventAwareness enum with two modes:
  - present_only: agent can only see events that are underway, and only current info.
  - omniscient: agent can see full event timing details.
  Default is present_only. (core/event.py)
- Added EventSummary and included events in SystemState. (core/simulation_state.py)
- Engine now emits event summaries with awareness-based info masking and excludes future-only fields for present_only events. (core/engine.py)
- System prompt updated to document event visibility rules. (core/system_prompt.py)

## Objectives: Agent Visibility
- Added ObjectiveSummary and included objectives in SystemState. (core/simulation_state.py)
- Engine now emits objective summaries every tick with status, timing, and custom fields. (core/engine.py)
- System prompt updated to include objective visibility. (core/system_prompt.py)

## Observation Layer (Partial Observability)
- Introduced an Observation layer so the agent sees only filtered, agent-facing data rather than raw world/system state. (core/observation.py)
- Added DefaultObservationPolicy with allowlists for world and system keys. (core/observation_policy.py)
- Scenario now accepts an optional observation_policy. (core/scenario.py)
- ScenarioRunner now builds an Observation per turn and sends only that to the agent. (core/scenario_runner.py)
- System prompt updated to clarify that observations may be filtered (partial observability). (core/system_prompt.py)

## Structured Observation JSON
- Observation payloads in prompts are now valid JSON (via json.dumps) to avoid parsing ambiguity. (core/scenario_runner.py)

## YAML-Driven Scenario Configuration
- Rewrote scripts/simple_scenario.py to load a YAML config and construct the scenario from registries. Behavior classes remain in Python; YAML selects and configures them. (scripts/simple_scenario.py)
- Added scripts/simple_scenario.yaml containing scenario definition, observation policy, system prompt instructions, and runner config. (scripts/simple_scenario.yaml)
- Added PyYAML dependency to pyproject.toml. (pyproject.toml)

## Notes and Usage
- The agent prompt now looks like: "Observation at tick X: {json}" where the JSON includes tick, world_state, system_state, and extras.
- Events default to present_only awareness. To make an event omniscient, set awareness to "omniscient" in YAML or in the event constructor.
- The NoOpAction prevents crashes when the agent chooses do_nothing.

## Files Added
- core/observation.py
- core/observation_policy.py
- scripts/simple_scenario.yaml
- SESSION_UPDATES.md

## Files Modified
- core/action.py
- core/engine.py
- core/event.py
- core/scenario.py
- core/scenario_runner.py
- core/simulation_state.py
- core/system_prompt.py
- scripts/simple_scenario.py
- pyproject.toml
