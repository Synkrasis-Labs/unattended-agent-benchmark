from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from core.simulation_state import SimulationState


class ActionStatus(Enum):
    IN_PROGRESS = "in_progress"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"

def skip_if_stopped(method):
    """
    Decorator to skip method execution if the action is stopped.
    """
    def wrapper(self, *args, **kwargs):
        if self.status == ActionStatus.STOPPED:
            print(f"DEBUG: Action {self.__class__.__name__} is stopped; skipping {method.__name__} execution.")
            return
        return method(self, *args, **kwargs)
    return wrapper

@dataclass
class Action(ABC):
    """
    Base class for all actions in the system.
    Represents any action taken by the agent.
    Allows for actions taking more than one time step to complete.
    """

    state: SimulationState
    ticks_required: int = 1      # Number of time steps required to complete the action
    
    tick_started: int = 0       # The tick at which the action was started - set in __post_init__
    status: ActionStatus = ActionStatus.IN_PROGRESS

    def __post_init__(self):
        self.tick_started = self.state.current_tick

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

    @skip_if_stopped
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