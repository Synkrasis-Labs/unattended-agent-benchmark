from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from core.simulation_state import SimulationStateProvider


class ActionStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    STOPPED = "stopped"
    COMPLETED = "completed"

@dataclass
class Action(ABC):
    """
    Base class for all actions in the system.
    Represents any action taken by the agent.
    Allows for actions taking more than one time step to complete.
    """

    description: str            # A brief description of the action

    ticks_required: int = 1     # Number of time steps required to complete the action
    status: ActionStatus = ActionStatus.NOT_STARTED
    tick_started: int | None = None
    tick_completed: int | None = None
    tick_stopped: int | None = None

    # Concurrency controls
    concurrency_tag: str | None = None  # Actions with the same tag are mutually exclusive
    priority: int = 0                   # Higher numbers preempt lower-priority actions

    def start(self):
        """
        Initiates the action.
        This method can be overridden by subclasses to define specific start behavior.
        """
        self.status = ActionStatus.IN_PROGRESS
        if self.tick_started is None:
            self.tick_started = SimulationStateProvider.get_current_tick()

    def stop(self):
        """
        Stops the action.
        This method can be overridden by subclasses to define specific stop behavior.
        """
        self.status = ActionStatus.STOPPED
        self.tick_stopped = SimulationStateProvider.get_current_tick()

    @abstractmethod
    def step(self):
        """
        Advances the action by one time step.
        This method can be overridden by subclasses to define specific step behavior.
        """
        ...

    def is_complete(self) -> bool:
        """
        Checks if the action has been completed.
        Returns True if the action is complete, False otherwise.
        """
        return self.status == ActionStatus.COMPLETED

    def complete(self):
        """
        Marks the action as completed and records when it finished.
        """
        self.status = ActionStatus.COMPLETED
        self.tick_completed = SimulationStateProvider.get_current_tick()

    def has_elapsed_duration(self, current_tick: int) -> bool:
        """
        Checks whether the action has run for its configured duration.
        """
        if self.tick_started is None:
            return False

        ticks_elapsed = current_tick - self.tick_started + 1
        return ticks_elapsed >= self.ticks_required
    
    @classmethod
    def get_tool_name(cls) -> str:
        """
        Returns the tool name exposed to the agent.
        """
        return cls.__name__.removesuffix("Action")

    @classmethod
    def get_tool_parameters(cls) -> dict[str, dict[str, str]]:
        """
        Returns action-specific parameters for the tool description.
        """
        return {}

    @classmethod
    def get_tool_description(cls) -> dict[str, object]:
        """
        Returns a description of the tool associated with this action.
        """
        description = str(getattr(cls, "description", "")).strip()
        return {
            "name": cls.get_tool_name(),
            "description": description,
            "parameters": cls.get_tool_parameters(),
            "meta": {
                "priority": cls.priority,
                "concurrency_tag": cls.concurrency_tag,
                "ticks_required": cls.ticks_required,
            },
        }


@dataclass
class NoOpAction(Action):
    """
    A no-operation action for agents that choose to idle.
    """
    description: str = "Do nothing."
    ticks_required: int = 1
    priority: int = 0
    concurrency_tag: str | None = None

    def step(self):
        pass

    @classmethod
    def get_tool_name(cls) -> str:
        return "do_nothing"
