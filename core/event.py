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

    tick_duration: int # Duration of the event in ticks
    status: EventStatus = EventStatus.NOT_STARTED

    @abstractmethod
    def start(self):
        """
        Starts the event.
        This method should be overridden by subclasses to define specific event behavior.
        """
        ...

    @abstractmethod
    def step(self):
        """
        Advances the event by one time step.
        This method should be overridden by subclasses to define specific event behavior.
        """
        ...
