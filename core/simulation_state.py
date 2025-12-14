from dataclasses import dataclass


@dataclass
class SimulationState:
    """
    A class representing the state of the simulation environment.
    It holds all relevant information about the current state of the environment.
    """

    tick_started: int = 0
    current_tick: int = 0