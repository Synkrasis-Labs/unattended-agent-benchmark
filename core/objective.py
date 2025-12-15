import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from core.simulation_state import SimulationStateProvider


def stochastic(func):
    """
    Stochastically execute methods decorated with this.
    Assumes that parent class has a 'probability' attribute.
    """
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, 'probability'):
            raise AttributeError("Stochastic methods require a 'probability' attribute.")
        
        if random.random() > self.probability:
            return  # Skip execution based on probability

        return func(self, *args, **kwargs)
    return wrapper

class ObjectiveStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Objective(ABC):
    """
    Base class for all objectives in the system.
    """

    tick_start: int    # Tick at which the objective is scheduled to start
    tick_done: int | None = None  # Tick at which the objective was completed or failed
    status: ObjectiveStatus = ObjectiveStatus.NOT_STARTED

    def start(self):
        """
        Starts the objective.
        This method should be overridden by subclasses to define specific objective behavior.
        """
        self.status = ObjectiveStatus.IN_PROGRESS

    def check_completion(self):
        """
        Advances the objective by one time step.
        This method can be overridden by subclasses to define specific objective behavior.
        """
        if self.status != ObjectiveStatus.IN_PROGRESS:
            return

        if self.is_completed(SimulationStateProvider.state):
            self.status = ObjectiveStatus.COMPLETED
            self.tick_done = SimulationStateProvider.get_current_tick()
        elif self.is_failed(SimulationStateProvider.state):
            self.status = ObjectiveStatus.FAILED
            self.tick_done = SimulationStateProvider.get_current_tick()

    @abstractmethod
    def is_completed(self, state) -> bool:
        """
        Checks if the objective is completed based on the current simulation state.
        This method should be overridden by subclasses to define specific completion criteria.
        """
        ...

    @abstractmethod
    def is_failed(self, state) -> bool:
        """
        Checks if the objective has failed based on the current simulation state.
        This method should be overridden by subclasses to define specific failure criteria.
        """
        ...

class StochasticObjective(Objective):
    """
    An objective with a stochastic step.
    """

    probability: float  # Probability factor influencing the stochastic behavior

    @stochastic
    @abstractmethod
    def check_completion(self):
        """
        Advances the stochastic objective by one time step.
        This method should incorporate randomness in its implementation.
        """
        ...
