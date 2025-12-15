from dataclasses import dataclass
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
