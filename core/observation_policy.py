from dataclasses import asdict
from typing import Protocol

from core.observation import Observation
from core.simulation_state import SimulationState, SystemState


class ObservationPolicy(Protocol):
    def build(
        self,
        tick: int,
        world_state: SimulationState,
        system_state: SystemState,
    ) -> Observation:
        ...


class DefaultObservationPolicy:
    """
    Default policy that exposes full world and system state unless filtered.
    """

    def __init__(
        self,
        world_keys: set[str] | None = None,
        system_keys: set[str] | None = None,
    ) -> None:
        self.world_keys = world_keys
        self.system_keys = system_keys

    def build(
        self,
        tick: int,
        world_state: SimulationState,
        system_state: SystemState,
    ) -> Observation:
        world_data = asdict(world_state)
        system_data = asdict(system_state)
        if self.world_keys is not None:
            world_data = _filter_keys(world_data, self.world_keys)
        if self.system_keys is not None:
            system_data = _filter_keys(system_data, self.system_keys)
        return Observation(
            tick=tick,
            world_state=world_data,
            system_state=system_data,
        )


def _filter_keys(data: dict[str, object], keys: set[str]) -> dict[str, object]:
    return {key: value for key, value in data.items() if key in keys}
