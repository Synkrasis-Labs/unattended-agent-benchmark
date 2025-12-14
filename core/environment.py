from abc import ABC, abstractmethod
from dataclasses import dataclass

from core.simulation_state import SimulationState


@dataclass
class Environment(ABC):
    """
    A class representing the environment where the agent operates.
    It manages the passive world dynamics of the simulation.
    """

    state: SimulationState

    @abstractmethod
    def step(self):
        """
        Advances the environment by one time step.
        This method should update the state of the environment based on its dynamics.
        """
        ...