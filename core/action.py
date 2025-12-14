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

    ticks_required: int = 1      # Number of time steps required to complete the action
    
    tick_started: int = 0       # The tick at which the action was started - set in __post_init__
    status: ActionStatus = ActionStatus.NOT_STARTED

    def __post_init__(self):
        state = SimulationStateProvider.get_state()
        self.tick_started = state.current_tick if state else 0

    @abstractmethod
    def start(self):
        """
        Initiates the action.
        This method can be overridden by subclasses to define specific start behavior.
        """
        ...

    @abstractmethod
    def stop(self):
        """
        Stops the action.
        This method can be overridden by subclasses to define specific stop behavior.
        """
        self.status = ActionStatus.STOPPED

    @abstractmethod
    def step(self):
        """
        Advances the action by one time step.
        This method can be overridden by subclasses to define specific step behavior.
        """
        ...
    
    @abstractmethod
    def is_complete(self) -> bool:
        """
        Checks if the action has been completed.
        Returns True if the action is complete, False otherwise.
        """
        return self.status == ActionStatus.COMPLETED
