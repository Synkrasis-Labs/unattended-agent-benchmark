from dataclasses import dataclass, field

from core.action import Action, ActionStatus
from core.environment import Environment
from core.event import Event, EventStatus
from core.objective import Objective, ObjectiveStatus
from core.simulation_state import SimulationStateProvider


@dataclass
class Engine:
    """
    The main simulation engine responsible for managing the simulation state,
    including the execution of objectives and the progression of time.
    """

    environment: Environment
    actions: list[Action] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    objectives: list[Objective] = field(default_factory=list)

    def step(self):
        """
        Advances the simulation by one time step.
        This method updates the simulation state and triggers any necessary events.
        """
        current_tick = SimulationStateProvider.get_current_tick()

        # 1. Advance the environment
        self.environment.step()

        # 2. Advance in-progress actions
        for action in self.actions:
            match action.status:
                case ActionStatus.IN_PROGRESS:
                    action.step()
                    if action.status is ActionStatus.IN_PROGRESS and action.has_elapsed_duration(current_tick):
                        action.complete()
                case ActionStatus.NOT_STARTED:
                    action.start()
            print("==== Action ====")
            print("Current Tick: "+ str(current_tick))
            print(action.get_tool_description)
            print("Started: "+ str(action.tick_started))
            print("Completed: "+ str(action.tick_completed))
            print("Stopped: "+ str(action.tick_stopped))
            print("Priority: "+ str(action.priority))
            print("==== ====")

        # 3. Advance events and objectives
        for event in self.events:
            if event.status is EventStatus.NOT_STARTED and current_tick >= event.tick_start:
                event.start()

            if event.status is EventStatus.IN_PROGRESS:
                event.step()

                if event.has_elapsed_duration(current_tick):
                    event.complete()
            print(str(current_tick)+"  " +str(event.status))

        # 4. Advance objectives
        for objective in self.objectives:
            match objective.status:
                case ObjectiveStatus.IN_PROGRESS:
                    objective.check_completion()
                case ObjectiveStatus.NOT_STARTED:
                    objective.start()

    def execute_action(self, action_cls: type[Action], parameters: dict):
        """
        Executes a given action with the specified parameters.
        This method adds the action to the list of active actions in the simulation.
        """
        # create an instance of the action
        action_instance = action_cls(**parameters)

        # Determine whether the new action can run alongside current actions
        conflicting_actions = [
            action for action in self.actions if action.status is ActionStatus.IN_PROGRESS
            and self._can_run_simultaneously(action, action_instance)
        ]
        print("Conflicting Actions:")
        print(conflicting_actions)
        if not conflicting_actions:
            self.actions.append(action_instance)
            return

        highest_conflict_priority = max(action.priority for action in conflicting_actions)
        print("Highest Conflict Priority: "+ str(highest_conflict_priority))
        print("Action Instance Priority: "+ str(action_instance.priority))
        if highest_conflict_priority >= action_instance.priority:
            # Existing actions of higher or equal priority keep running; discard the new one
            return

        # New action preempts lower-priority conflicting actions
        for action in conflicting_actions:
            action.stop()

        self.actions.append(action_instance)

    @staticmethod
    def _can_run_simultaneously(action_a: Action, action_b: Action) -> bool:
        """Checks if two actions can run at the same time based on their group tags."""
        if action_a.concurrency_tag is None or action_b.concurrency_tag is None:
            return True
        return action_a.concurrency_tag != action_b.concurrency_tag

    def metrics(self) -> dict:
        """
        Collects and returns metrics about the current state of the simulation.
        This can include information about objectives, actions taken, and environment state.
        """
        ...