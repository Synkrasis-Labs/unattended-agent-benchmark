import threading
import time
from dataclasses import asdict, dataclass

from core.engine import Engine
from core.monkey_patch import MonkeyPatch
from core.scenario import Scenario
from core.simulation_state import SimulationStateProvider


@dataclass
class ScenarioRunnerConfig:
    """
    Configuration for the ScenarioRunner.
    """
    max_ticks: int | None = 1000      # Maximum number of ticks to run the scenario - None for unlimited
    agent_delay_ticks: int = 0        # Number of ticks to wait before starting the agent
    agent_tick_interval: int = 5      # Number of ticks between agent invocations
    real_time_delay_s: float = 0.1    # Real time delay in seconds between ticks

@dataclass
class ScenarioRunner:
    """
    The main entry point for running scenarios.
    """

    config: ScenarioRunnerConfig

    def run(self, scenario: Scenario):
        """
        Runs the given scenario.
        """
        
        # create scenario engine
        engine = Engine(
            environment=scenario.environment,
            events=scenario.events,
            objectives=scenario.objectives,
        )

        # create agent
        agent = MonkeyPatch.get_agent(system_prompt=scenario.system_prompt)

        running_condition = lambda _: True
        if self.config.max_ticks is not None:
            running_condition = lambda current_tick: current_tick < self.config.max_ticks

        lock = threading.Lock()

        # run agent and simulation in two separate threads
        def _simulation_loop():
            while True:
                # wait for lock
                lock.acquire()
                state = SimulationStateProvider.state
                if state is None or not running_condition(state.current_tick):
                    break
                engine.step()
                state.current_tick += 1
                lock.release()
                time.sleep(self.config.real_time_delay_s)

        def _agent_loop():

            # wait for initial delay
            for _ in range(self.config.agent_delay_ticks):
                time.sleep(self.config.real_time_delay_s)

            while True:
                lock.acquire()
                input("Press Enter to let the agent take its turn...")
                state = SimulationStateProvider.state
                if state is None or not running_condition(state.current_tick):
                    break
                ct = state.current_tick
                prompt = f"Simulation State at tick {ct}: {asdict(state)}"
                print(f"Agent Prompt at tick {ct}: {prompt}")

                llm_output, parsed_action, metadata = MonkeyPatch.step_agent(agent, prompt)
                print(f"Agent Thought at tick {ct}: {llm_output}")

                if parsed_action is not None:
                    # create action instance
                    print(f"parsed_action: {parsed_action}")
                    action_cls = scenario.action_registry.get(parsed_action.tool_name, None)
                    if action_cls is None:
                        raise ValueError(f"Action '{parsed_action.tool_name}' not found in action registry.")

                    engine.execute_action(action_cls, parsed_action.arguments)

                lock.release()
                for _ in range(self.config.agent_tick_interval):
                    time.sleep(self.config.real_time_delay_s)

        agent_thread = threading.Thread(target=_agent_loop)
        simulation_thread = threading.Thread(target=_simulation_loop)

        agent_thread.start()
        simulation_thread.start()

        agent_thread.join()
        simulation_thread.join()
