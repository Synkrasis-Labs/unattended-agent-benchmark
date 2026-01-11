from dataclasses import dataclass, field
from typing import Generic, TypeVar

SimulationStateType = TypeVar("SimulationStateType", bound="SimulationState")


@dataclass
class SimulationState:
    """
    A class representing the state of the simulation environment.
    It holds all relevant information about the current state of the environment.
    """
    tick_started: int = 0
    current_tick: int = 0

class SimulationStateProvider(Generic[SimulationStateType]):
    """
    A singleton class that provides access to the current simulation state.
    """
    def __init__(self, state: SimulationStateType) -> None:
        self.state: SimulationStateType = state

    @staticmethod
    def get_current_tick() -> int:
        return SimulationStateProvider.state.current_tick

    @staticmethod
    def advance_tick() -> None:
        SimulationStateProvider.state.current_tick += 1


@dataclass
class ActionSummary:
    """
    A lightweight snapshot of an action for agent-facing system state.
    """
    name: str
    status: str
    concurrency_tag: str | None
    priority: int
    tick_started: int | None
    ticks_required: int
    ticks_elapsed: int
    ticks_remaining: int
    tick_completed: int | None = None
    tick_stopped: int | None = None
    parameters: dict[str, object] = field(default_factory=dict)


@dataclass
class ActionFeedback:
    """
    Structured feedback about the last action request.
    """
    requested_action: str
    arguments: dict[str, object]
    accepted: bool
    reason: str
    tick: int
    conflicts: list[ActionSummary] = field(default_factory=list)
    preempted: list[ActionSummary] = field(default_factory=list)
    started_action: ActionSummary | None = None


@dataclass
class SystemState:
    """
    Agent-facing system state: running actions and last action feedback.
    """
    running_actions: list[ActionSummary] = field(default_factory=list)
    events: list["EventSummary"] = field(default_factory=list)
    objectives: list["ObjectiveSummary"] = field(default_factory=list)
    last_action_feedback: ActionFeedback | None = None


class SystemStateProvider:
    """
    Singleton provider for system state presented to the agent.
    """
    state: SystemState = SystemState()


@dataclass
class EventSummary:
    """
    A lightweight snapshot of an event for agent-facing system state.
    """
    name: str
    description: str
    status: str
    awareness: str
    info: dict[str, object] = field(default_factory=dict)
    parameters: dict[str, object] = field(default_factory=dict)


@dataclass
class ObjectiveSummary:
    """
    A lightweight snapshot of an objective for agent-facing system state.
    """
    name: str
    description: str
    status: str
    tick_start: int
    tick_done: int | None
    ticks_elapsed: int
    parameters: dict[str, object] = field(default_factory=dict)
