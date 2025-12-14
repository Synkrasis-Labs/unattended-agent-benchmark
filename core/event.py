from abc import ABC, abstractmethod
from dataclasses import dataclass

from core.simulation_state import SimulationState


@dataclass
class Event(ABC):
    """
    Base class for all events in the system.
    """
    
    tick_duration: int # Duration of the event in ticks
    state: SimulationState

    @abstractmethod
    def step(self):
        """
        Advances the event by one time step.
        This method should be overridden by subclasses to define specific event behavior.
        """
        ...