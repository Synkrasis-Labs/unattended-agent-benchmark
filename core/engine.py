from dataclasses import dataclass, field

from core.action import Action, ActionStatus
from core.environment import Environment
from core.event import Event, EventAwareness, EventStatus
from core.objective import Objective, ObjectiveStatus
from core.simulation_state import (
    ActionFeedback,
    ActionSummary,
    EventSummary,
    ObjectiveSummary,
    SimulationStateProvider,
    SystemStateProvider,
)


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
            print(
                "[tick {tick}] action={name} status={status} started={started} "
                "completed={completed} stopped={stopped} priority={priority} tag={tag}"
                .format(
                    tick=current_tick,
                    name=action.__class__.__name__,
                    status=action.status.value,
                    started=action.tick_started,
                    completed=action.tick_completed,
                    stopped=action.tick_stopped,
                    priority=action.priority,
                    tag=action.concurrency_tag,
                )
            )

        # 3. Advance events and objectives
        for event in self.events:
            if event.status is EventStatus.NOT_STARTED and current_tick >= event.tick_start:
                event.start()

            if event.status is EventStatus.IN_PROGRESS:
                event.step()

                if event.has_elapsed_duration(current_tick):
                    event.complete()
            print(
                "[tick {tick}] event={name} status={status} started={started} completed={completed}"
                .format(
                    tick=current_tick,
                    name=event.__class__.__name__,
                    status=event.status.value,
                    started=event.tick_started,
                    completed=event.tick_completed,
                )
            )

        # 4. Advance objectives
        for objective in self.objectives:
            match objective.status:
                case ObjectiveStatus.IN_PROGRESS:
                    objective.check_completion()
                case ObjectiveStatus.NOT_STARTED:
                    objective.start()

        self._refresh_system_state(current_tick)

    def execute_action(self, action_cls: type[Action], parameters: dict):
        """
        Executes a given action with the specified parameters.
        This method adds the action to the list of active actions in the simulation.
        """
        current_tick = SimulationStateProvider.get_current_tick()

        # create an instance of the action
        action_instance = action_cls(**parameters)

        # Determine whether the new action can run alongside current actions
        conflicting_actions = [
            action
            for action in self.actions
            if action.status is ActionStatus.IN_PROGRESS
            and not self._can_run_simultaneously(action, action_instance)
        ]
        print(
            "conflicts: [{names}]".format(
                names=", ".join(action.__class__.__name__ for action in conflicting_actions)
            )
        )
        conflict_summaries = [
            self._build_action_summary(action, current_tick)
            for action in conflicting_actions
        ]
        if not conflicting_actions:
            self.actions.append(action_instance)
            SystemStateProvider.state.last_action_feedback = ActionFeedback(
                requested_action=action_cls.get_tool_name(),
                arguments=parameters,
                accepted=True,
                reason="accepted_no_conflict",
                tick=current_tick,
                conflicts=[],
                preempted=[],
                started_action=self._build_action_summary(action_instance, current_tick),
            )
            self._refresh_system_state(current_tick)
            return

        highest_conflict_priority = max(action.priority for action in conflicting_actions)
        print(
            "conflict_priorities: highest={highest} incoming={incoming}".format(
                highest=highest_conflict_priority,
                incoming=action_instance.priority,
            )
        )
        if highest_conflict_priority >= action_instance.priority:
            # Existing actions of higher or equal priority keep running; discard the new one
            SystemStateProvider.state.last_action_feedback = ActionFeedback(
                requested_action=action_cls.get_tool_name(),
                arguments=parameters,
                accepted=False,
                reason="rejected_higher_or_equal_priority_conflict",
                tick=current_tick,
                conflicts=conflict_summaries,
                preempted=[],
                started_action=None,
            )
            self._refresh_system_state(current_tick)
            return

        # New action preempts lower-priority conflicting actions
        for action in conflicting_actions:
            action.stop()

        preempted_summaries = [
            self._build_action_summary(action, current_tick)
            for action in conflicting_actions
        ]

        self.actions.append(action_instance)
        SystemStateProvider.state.last_action_feedback = ActionFeedback(
            requested_action=action_cls.get_tool_name(),
            arguments=parameters,
            accepted=True,
            reason="accepted_preempted_lower_priority",
            tick=current_tick,
            conflicts=conflict_summaries,
            preempted=preempted_summaries,
            started_action=self._build_action_summary(action_instance, current_tick),
        )
        self._refresh_system_state(current_tick)

    @staticmethod
    def _can_run_simultaneously(action_a: Action, action_b: Action) -> bool:
        """Checks if two actions can run at the same time based on their group tags."""
        if action_a.concurrency_tag is None or action_b.concurrency_tag is None:
            return True
        return action_a.concurrency_tag != action_b.concurrency_tag

    @staticmethod
    def _action_parameters(action: Action) -> dict[str, object]:
        base_fields = {
            "description",
            "ticks_required",
            "status",
            "tick_started",
            "tick_completed",
            "tick_stopped",
            "concurrency_tag",
            "priority",
        }
        return {
            key: value
            for key, value in action.__dict__.items()
            if key not in base_fields
        }

    def _build_action_summary(self, action: Action, current_tick: int) -> ActionSummary:
        if action.tick_started is None:
            ticks_elapsed = 0
        else:
            ticks_elapsed = max(current_tick - action.tick_started + 1, 0)

        ticks_remaining = max(action.ticks_required - ticks_elapsed, 0)
        return ActionSummary(
            name=action.__class__.get_tool_name(),
            status=action.status.value,
            concurrency_tag=action.concurrency_tag,
            priority=action.priority,
            tick_started=action.tick_started,
            ticks_required=action.ticks_required,
            ticks_elapsed=ticks_elapsed,
            ticks_remaining=ticks_remaining,
            tick_completed=action.tick_completed,
            tick_stopped=action.tick_stopped,
            parameters=self._action_parameters(action),
        )

    @staticmethod
    def _event_parameters(event: Event) -> dict[str, object]:
        base_fields = {
            "tick_start",
            "tick_duration",
            "status",
            "tick_started",
            "tick_completed",
            "awareness",
            "description",
        }
        return {
            key: value
            for key, value in event.__dict__.items()
            if key not in base_fields
        }

    def _build_event_summary(self, event: Event, current_tick: int) -> EventSummary:
        if event.tick_started is None:
            ticks_elapsed = 0
        else:
            ticks_elapsed = max(current_tick - event.tick_started + 1, 0)

        ticks_remaining = max(event.tick_duration - ticks_elapsed, 0)
        awareness = event.awareness
        info: dict[str, object] = {}
        if awareness is EventAwareness.OMNISCIENT:
            info = {
                "tick_start": event.tick_start,
                "tick_duration": event.tick_duration,
                "tick_started": event.tick_started,
                "tick_completed": event.tick_completed,
                "ticks_elapsed": ticks_elapsed,
                "ticks_remaining": ticks_remaining,
            }
        else:
            info = {
                "tick_started": event.tick_started,
                "ticks_elapsed": ticks_elapsed,
            }
        return EventSummary(
            name=event.__class__.__name__,
            description=str(getattr(event, "description", "")).strip(),
            status=event.status.value,
            awareness=awareness.value,
            info=info,
            parameters=self._event_parameters(event),
        )

    def _refresh_system_state(self, current_tick: int) -> None:
        SystemStateProvider.state.running_actions = [
            self._build_action_summary(action, current_tick)
            for action in self.actions
            if action.status is ActionStatus.IN_PROGRESS
        ]
        SystemStateProvider.state.events = [
            self._build_event_summary(event, current_tick)
            for event in self.events
            if (
                (event.awareness is EventAwareness.OMNISCIENT and event.status is not EventStatus.COMPLETED)
                or (event.awareness is EventAwareness.PRESENT_ONLY and event.status is EventStatus.IN_PROGRESS)
            )
        ]
        SystemStateProvider.state.objectives = [
            self._build_objective_summary(objective, current_tick)
            for objective in self.objectives
        ]

    @staticmethod
    def _objective_parameters(objective: Objective) -> dict[str, object]:
        base_fields = {
            "tick_start",
            "tick_done",
            "status",
            "description",
        }
        return {
            key: value
            for key, value in objective.__dict__.items()
            if key not in base_fields
        }

    def _build_objective_summary(
        self, objective: Objective, current_tick: int
    ) -> ObjectiveSummary:
        if current_tick < objective.tick_start:
            ticks_elapsed = 0
        else:
            ticks_elapsed = max(current_tick - objective.tick_start + 1, 0)

        return ObjectiveSummary(
            name=objective.__class__.__name__,
            description=str(getattr(objective, "description", "")).strip(),
            status=objective.status.value,
            tick_start=objective.tick_start,
            tick_done=objective.tick_done,
            ticks_elapsed=ticks_elapsed,
            parameters=self._objective_parameters(objective),
        )

    def metrics(self) -> dict:
        """
        Collects and returns metrics about the current state of the simulation.
        This can include information about objectives, actions taken, and environment state.
        """
        ...
