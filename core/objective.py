import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


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

    status: ObjectiveStatus = ObjectiveStatus.NOT_STARTED

    @abstractmethod
    def start(self):
        """
        Starts the objective.
        This method should be overridden by subclasses to define specific objective behavior.
        """
        ...

    @abstractmethod
    def step(self):
        """
        Advances the objective by one time step.
        This method can be overridden by subclasses to define specific objective behavior.
        """
        ...

class StochasticObjective(Objective):
    """
    An objective with a stochastic step.
    """

    probability: float  # Probability factor influencing the stochastic behavior

    @stochastic
    @abstractmethod
    def step(self):
        """
        Advances the stochastic objective by one time step.
        This method should incorporate randomness in its implementation.
        """
        ...
