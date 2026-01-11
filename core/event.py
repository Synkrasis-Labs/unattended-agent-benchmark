from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from core.simulation_state import SimulationStateProvider


class EventStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class EventAwareness(Enum):
    PRESENT_ONLY = "present_only"
    OMNISCIENT = "omniscient"

@dataclass
class Event(ABC):
    """
    Base class for all events in the system.
    """

    tick_start: int  # Tick at which the event is scheduled to start
    tick_duration: int  # Duration of the event in ticks
    status: EventStatus = EventStatus.NOT_STARTED
    tick_started: int | None = None
    tick_completed: int | None = None
    awareness: EventAwareness = EventAwareness.PRESENT_ONLY

    def start(self):
        """
        Starts the event.
        This method should be overridden by subclasses to define specific event behavior.
        """
        self.status = EventStatus.IN_PROGRESS
        self.tick_started = SimulationStateProvider.get_current_tick()

    def complete(self):
        """
        Completes the event.
        """
        self.status = EventStatus.COMPLETED
        self.tick_completed = SimulationStateProvider.get_current_tick()

    def has_elapsed_duration(self, current_tick: int) -> bool:
        """
        Checks whether the event has run for its configured duration.
        """
        if self.tick_started is None:
            return False

        ticks_elapsed = current_tick - self.tick_started + 1
        return ticks_elapsed >= self.tick_duration

    @abstractmethod
    def step(self):
        """
        Advances the event by one time step.
        This method should be overridden by subclasses to define specific event behavior.
        """
        ...
