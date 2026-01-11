from dataclasses import dataclass, field


@dataclass
class Observation:
    """
    Agent-facing observation derived from world and system state.
    """
    tick: int
    world_state: dict[str, object] = field(default_factory=dict)
    system_state: dict[str, object] = field(default_factory=dict)
    extras: dict[str, object] = field(default_factory=dict)
