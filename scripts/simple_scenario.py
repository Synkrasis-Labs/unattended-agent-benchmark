from dataclasses import dataclass

from core.action import Action
from core.environment import Environment
from core.event import Event
from core.objective import Objective
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
    
sr = ScenarioRunner(
    config=ScenarioRunnerConfig(
        max_ticks=500,
        agent_delay_ticks=0,
        agent_tick_interval=1,
        real_time_delay_s=0.1
    )
)
scenario = Scenario(
    name="Simple Scenario",
    description="A simple scenario with a basic environment, no events, and a single objective.",
    environment=SimpleEnvironment(),
    action_registry={
        "Fertilize": FertilizeAction,
        "WaterTrees": WaterTreesAction,
    },
    events=[
        BadWeatherEvent(tick_start=5, tick_duration=3),
        GoodWeatherEvent(tick_start=1, tick_duration=2)
    ],
    objectives=[GrowTreesObjective(tick_start=2, target_growth=10.0),
                GrowTreeQuicklyObjective(tick_start=1, target_growth=15.0, max_ticks=20)],
    system_prompt=build_system_prompt(
        custom_instructions=(
            "You are an agent tasked with growing trees in a simple environment. "
            "On your first turn, request Fertilize and on your second turn request the Watering action even if the fertilizing is already running."
        ),
        custom_tools=str([FertilizeAction.get_tool_description(), WaterTreesAction.get_tool_description()])
    )
)

sr.run(scenario)
