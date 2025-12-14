from typing import Any, NamedTuple, TypeVar

from are.simulation.agents.are_simulation_agent import RunnableARESimulationAgent
from are.simulation.agents.are_simulation_agent_config import (
    LLMEngineConfig,
    MainAgentConfig,
    RunnableARESimulationAgentConfig,
)
from are.simulation.agents.llm.types import MessageRole
from are.simulation.environment import Environment, EnvironmentConfig, EnvironmentType
from are.simulation.exceptions import InvalidActionAgentError
from are.simulation.scenario_runner import ScenarioRunner
from are.simulation.types import SimulatedGenerationTimeConfig

from .system_prompt import SYSTEM_PROMPT

Agent = TypeVar("Agent", bound=Any)
Prompt = TypeVar("Prompt", bound=list[dict[str, str]])

AgentProvider = NamedTuple("AgentProvider", [("react_agent", Agent), ("prompt", Prompt)])

def scenario_runner_monkey_patch(
    self,
    env: Environment,
    agent: str,
    model: str,
    provider: str | None = None,
    endpoint: str | None = None,
    max_turns: int | None = None,
    simulated_generation_time_mode: str = "measured",
    use_custom_logger: bool = True,
):
    agent_config: RunnableARESimulationAgentConfig = (
        self.agent_config_builder.build(agent_name=agent)
    )

    # Set the use_custom_logger parameter in the base agent config
    agent_config.get_base_agent_config().use_custom_logger = use_custom_logger
    agent_config.get_base_agent_config().llm_engine_config = LLMEngineConfig(
        model_name=model, provider=provider, endpoint=endpoint
    )

    # Create SimulatedGenerationTimeConfig from the mode
    simulated_generation_time_config = SimulatedGenerationTimeConfig(
        mode=simulated_generation_time_mode  # type: ignore
    )
    agent_config.get_base_agent_config().simulated_generation_time_config = (
        simulated_generation_time_config
    )

    if isinstance(agent_config, MainAgentConfig) and max_turns is not None:
        agent_config.max_turns = max_turns

    are_simulation_agent: RunnableARESimulationAgent = self.agent_builder.build(
        agent_config=agent_config, env=env
    )
    return are_simulation_agent

def agent_step_monkeypatch(self, prompt: list[dict[str, str]]) -> tuple[str | None, dict]:
    llm_output = None
    metadata = {}
    format_try_count: int = 0
    
    while llm_output is None or (
        self.retry_llm_call_on_error
        and self.action_token not in llm_output
        and self.thought_token not in llm_output
    ):
        if llm_output is not None:
            self.logger.warning(
                f"LLM did not return a valid output: {llm_output}.\nRetrying..."
            )
            self.log_error(
                InvalidActionAgentError(
                    f"The LLM output was not formatted correctly: {llm_output}"
                )
            )
        llm_response = self.llm_engine(
            prompt,
            stop_sequences=["<end_action>", "Observation:"],
            additional_trace_tags=["action"],
            schema=self.decoding_schema,
        )
        if isinstance(llm_response, tuple) and len(llm_response) == 2:
            llm_output, metadata = llm_response
        else:
            llm_output = llm_response
            metadata = {}

        format_try_count += 1
        # This is a failsafe from infinite loop issues that can happen when the input prompt is too long
        if format_try_count > self.invalid_format_retries:
            break

    if metadata is None: metadata = {}

    prompt.append(
        {
            "role": MessageRole.ASSISTANT,
            "content": llm_output,
            "attachments": None
        }
    )

    try:
        agent_action = self.action_executor.extract_action(
            llm_output=llm_output, split_token=self.action_token
        )
    except Exception as e:
        self.logger.error(f"Error while extracting action: {e}")
        self.logger.debug(f"LLM output: {llm_output}")
        raise e

    prompt.append(
        {
            "role": MessageRole.SYSTEM,
            "content": agent_action.rationale,
            "attachments": None
        }
    )

    parsed_action = None
    if agent_action.action is not None:
        # Parse the action
        parsed_action = self.action_executor.parse_action(agent_action)
    else:
        self.logger.warning(f"No action found in LLM output {llm_output}")

    return llm_output, parsed_action, metadata

class MonkeyPatch:
    
    @staticmethod
    def get_agent(
        model: str = "meta-llama/Llama-3.3-70B-Instruct",
        provider: str | None = "hyperbolic",
        architecture: str = "default",
        system_prompt: str = SYSTEM_PROMPT,
    ) -> AgentProvider:

        prompt = [
            {
                "role": MessageRole.SYSTEM,
                "content": system_prompt,
                "attachments": None
            },
        ]

        env_config = EnvironmentConfig(
            oracle_mode=False,
            queue_based_loop=False,
            wait_for_user_input_timeout=None,
            dump_dir=None,
            time_increment_in_seconds=1,
            exit_when_no_events=False,
        )

        dummy_env = Environment(
            environment_type=EnvironmentType.CLI,
            config=env_config,
            notification_system=None,
        )

        scenario_runner = ScenarioRunner()
        agent = scenario_runner_monkey_patch(
            scenario_runner,
            env=dummy_env,
            agent=architecture,
            model=model,
            provider=provider,
        )

        return AgentProvider(agent.react_agent, prompt)

    @staticmethod
    def step_agent(
        agent: AgentProvider, prompt: str
    ) -> None:
        agent.prompt.append(
            {
                "role": MessageRole.USER,
                "content": prompt,
            }
        )
        return agent_step_monkeypatch(agent.react_agent, agent.prompt)
