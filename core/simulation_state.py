from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

SimulationStateType = TypeVar('SimulationStateType', bound='SimulationState')

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

    _instance: SimulationStateProvider | None = None
    _state: SimulationStateType | None = None
    _state_class: type[SimulationStateType] | None = None

    def __new__(cls) -> SimulationStateProvider:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def set_state(cls, state: SimulationStateType) -> None:
        if cls._state_class is None:
            cls._state_class = type(state)

        assert isinstance(state, cls._state_class), (
            f"Expected state of type {cls._state_class.__name__}, "
            f"got {type(state).__name__}."
        )
        cls._state = state

    @classmethod
    def get_state(cls) -> SimulationStateType | None:
        return cls._state

    @classmethod
    def clear_state(cls) -> None:
        cls._state = None
        cls._state_class = None