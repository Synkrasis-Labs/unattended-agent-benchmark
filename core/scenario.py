from dataclasses import dataclass, field

from core.action import Action
from core.environment import Environment
from core.event import Event
from core.objective import Objective
from core.system_prompt import build_system_prompt


@dataclass
class Scenario:
    """
    Base class for all scenarios in the system.
    """
    
    name: str
    description: str

    environment: Environment
    action_registry: dict[str, Action] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)
    objectives: list[Objective] = field(default_factory=list)

    system_prompt: str = build_system_prompt()
    