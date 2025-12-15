from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class EventStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

@dataclass
class Event(ABC):
    """
    Base class for all events in the system.
    """

    tick_start: int    # Tick at which the event is scheduled to start
    tick_duration: int # Duration of the event in ticks
    status: EventStatus = EventStatus.NOT_STARTED

    def start(self):
        """
        Starts the event.
        This method should be overridden by subclasses to define specific event behavior.
        """
        self.status = EventStatus.IN_PROGRESS

    @abstractmethod
    def step(self):
        """
        Advances the event by one time step.
        This method should be overridden by subclasses to define specific event behavior.
        """
        ...
