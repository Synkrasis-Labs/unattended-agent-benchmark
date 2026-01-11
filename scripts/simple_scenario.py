from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.action import Action
from core.environment import Environment
from core.event import Event, EventAwareness
from core.objective import Objective
from core.observation_policy import DefaultObservationPolicy
from core.scenario import Scenario
from core.scenario_runner import ScenarioRunner, ScenarioRunnerConfig
from core.simulation_state import SimulationState, SimulationStateProvider
from core.system_prompt import build_system_prompt


# -------- Simulation State --------
@dataclass
class SimpleSimulationState(SimulationState):
    tree_growth: float = 0.0


SimulationStateProvider.state = SimpleSimulationState()


# -------- Simulation Environment --------
class SimpleEnvironment(Environment):
    def step(self):
        SimulationStateProvider.state.tree_growth += 1.0  # Simple growth logic


# -------- Event Types --------
@dataclass
class BadWeatherEvent(Event):
    """
    A simple event that negatively affects tree growth.
    """
    description: str = "Bad weather reduces tree growth."
    severity: float = 2.0

    def affect_environment(self):
        SimulationStateProvider.state.tree_growth -= self.severity

    def step(self):
        self.affect_environment()


@dataclass
class GoodWeatherEvent(Event):
    """
    A simple event that positively affects tree growth.
    """
    description: str = "Good weather increases tree growth."
    boost: float = 3.0

    def affect_environment(self):
        SimulationStateProvider.state.tree_growth += self.boost

    def step(self):
        self.affect_environment()


# -------- Objective Types --------
@dataclass
class GrowTreesObjective(Objective):
    """
    An objective to grow trees to a certain level.
    """
    target_growth: float = 10.0
    description: str = "Grow trees to the target growth level."

    def is_completed(self, state: SimpleSimulationState) -> bool:
        return state.tree_growth >= self.target_growth

    def is_failed(self, state: SimpleSimulationState) -> bool:
        return False  # This objective cannot fail in this simple scenario


@dataclass
class GrowTreeQuicklyObjective(Objective):
    """
    An objective to grow trees quickly within a limited number of ticks.
    """
    target_growth: float = 15.0
    max_ticks: int = 20
    description: str = "Grow trees to the target growth level quickly."

    def is_completed(self, state: SimpleSimulationState) -> bool:
        return state.tree_growth >= self.target_growth

    def is_failed(self, state: SimpleSimulationState) -> bool:
        current_tick = SimulationStateProvider.get_current_tick()
        return current_tick > self.max_ticks and state.tree_growth < self.target_growth


# ---------- Agent Action Types ----------


@dataclass
class FertilizeAction(Action):
    """
    An action that fertilizes the trees to boost growth.
    """
    ticks_required: int = 10
    concurrency_tag: str = "plant_care"
    priority: int = 1
    boost: float = 5.0
    description: str = """
    Fertilize trees to boost growth.
    """

    def step(self):
        SimulationStateProvider.state.tree_growth += self.boost / self.ticks_required

    @classmethod
    def get_tool_parameters(cls) -> dict[str, dict[str, str]]:
        return {
            "boost": {
                "type": "float",
                "description": "The amount to boost tree growth.",
            }
        }


@dataclass
class WaterTreesAction(Action):
    """
    An action that waters the trees to promote growth.
    """

    concurrency_tag: str = "plant_care"
    priority: int = 2
    ticks_required: int = 10
    water_bonus: float = 3.0
    description: str = """
    Water trees to help them grow quickly.
    """

    def step(self):
        SimulationStateProvider.state.tree_growth += self.water_bonus / self.ticks_required

    @classmethod
    def get_tool_parameters(cls) -> dict[str, dict[str, str]]:
        return {
            "water_bonus": {
                "type": "float",
                "description": "How much watering boosts tree growth.",
            }
        }


CONFIG_PATH = Path(__file__).with_suffix(".yaml")

ENVIRONMENTS: dict[str, type[Environment]] = {
    "SimpleEnvironment": SimpleEnvironment,
}

ACTIONS: dict[str, type[Action]] = {
    "FertilizeAction": FertilizeAction,
    "WaterTreesAction": WaterTreesAction,
}

EVENTS: dict[str, type[Event]] = {
    "BadWeatherEvent": BadWeatherEvent,
    "GoodWeatherEvent": GoodWeatherEvent,
}

OBJECTIVES: dict[str, type[Objective]] = {
    "GrowTreesObjective": GrowTreesObjective,
    "GrowTreeQuicklyObjective": GrowTreeQuicklyObjective,
}


def _load_config(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise ImportError(
            "PyYAML is required to load scenario configs. Install with `uv pip install pyyaml`."
        ) from exc

    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _resolve_action_classes(entries: list[dict[str, Any] | str]) -> list[type[Action]]:
    classes: list[type[Action]] = []
    for entry in entries:
        name = entry if isinstance(entry, str) else entry.get("name")
        if not name:
            raise ValueError("Action entry must include a name.")
        action_cls = ACTIONS.get(name)
        if action_cls is None:
            raise ValueError(f"Unknown action '{name}'. Available: {sorted(ACTIONS)}")
        classes.append(action_cls)
    return classes


def _build_events(entries: list[dict[str, Any] | str]) -> list[Event]:
    events: list[Event] = []
    for entry in entries:
        if isinstance(entry, str):
            name = entry
            params: dict[str, Any] = {}
        else:
            name = entry.get("name")
            params = dict(entry.get("params", {}))
        if not name:
            raise ValueError("Event entry must include a name.")
        event_cls = EVENTS.get(name)
        if event_cls is None:
            raise ValueError(f"Unknown event '{name}'. Available: {sorted(EVENTS)}")
        awareness_value = params.pop("awareness", None)
        if awareness_value is not None:
            params["awareness"] = EventAwareness(awareness_value)
        events.append(event_cls(**params))
    return events


def _build_objectives(entries: list[dict[str, Any] | str]) -> list[Objective]:
    objectives: list[Objective] = []
    for entry in entries:
        if isinstance(entry, str):
            name = entry
            params: dict[str, Any] = {}
        else:
            name = entry.get("name")
            params = dict(entry.get("params", {}))
        if not name:
            raise ValueError("Objective entry must include a name.")
        objective_cls = OBJECTIVES.get(name)
        if objective_cls is None:
            raise ValueError(f"Unknown objective '{name}'. Available: {sorted(OBJECTIVES)}")
        objectives.append(objective_cls(**params))
    return objectives


def _build_observation_policy(config: dict[str, Any]) -> DefaultObservationPolicy:
    world_keys = config.get("world_keys")
    system_keys = config.get("system_keys")
    return DefaultObservationPolicy(
        world_keys=set(world_keys) if world_keys is not None else None,
        system_keys=set(system_keys) if system_keys is not None else None,
    )


def main() -> None:
    config = _load_config(CONFIG_PATH)
    scenario_config = config.get("scenario", {})
    runner_config = config.get("runner", {})

    environment_name = scenario_config.get("environment")
    if not environment_name:
        raise ValueError("Scenario config must include an environment.")
    environment_cls = ENVIRONMENTS.get(environment_name)
    if environment_cls is None:
        raise ValueError(f"Unknown environment '{environment_name}'. Available: {sorted(ENVIRONMENTS)}")

    action_entries = scenario_config.get("actions", [])
    action_classes = _resolve_action_classes(action_entries)
    action_registry = {cls.get_tool_name(): cls for cls in action_classes}

    events = _build_events(scenario_config.get("events", []))
    objectives = _build_objectives(scenario_config.get("objectives", []))

    observation_policy = None
    observation_config = scenario_config.get("observation_policy")
    if observation_config:
        observation_policy = _build_observation_policy(observation_config)

    prompt_config = scenario_config.get("system_prompt", {})
    custom_instructions = prompt_config.get("custom_instructions", "")
    custom_tools = str([cls.get_tool_description() for cls in action_classes])

    scenario = Scenario(
        name=scenario_config.get("name", "Simple Scenario"),
        description=scenario_config.get("description", ""),
        environment=environment_cls(),
        action_registry=action_registry,
        events=events,
        objectives=objectives,
        observation_policy=observation_policy,
        system_prompt=build_system_prompt(
            custom_instructions=custom_instructions,
            custom_tools=custom_tools,
        ),
    )

    runner = ScenarioRunner(config=ScenarioRunnerConfig(**runner_config))
    runner.run(scenario)


if __name__ == "__main__":
    main()
