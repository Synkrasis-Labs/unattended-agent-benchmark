from core.monkey_patch import MonkeyPatch
from core.system_prompt import build_system_prompt

class SimpleChatTools:

    @staticmethod
    def echo(message: str) -> None:
        """A tool that echoes back the input provided by the user."""
        print(message)

    @staticmethod
    def send_message_to_user(message: str) -> None:
        """A tool that sends a message to the user in the chat interface."""
        print(f"Message to user: {message}")

SYSTEM_PROMPT = build_system_prompt(
    custom_instructions="You are a simple chat agent that responds to user inputs.",
    custom_tools='\n'.join([str(tool) for tool in [
        {
            "name": "echo",
            "description": "A tool that echoes back the input provided by the user.",
            "parameters": {
                "message": "The message to be echoed back."
            },
            "return_type": "string",
        },
        {
            "name": "send_message_to_user",
            "description": "A tool that sends a message to the user in the chat interface.",
            "parameters": {
                "message": "The message content to send to the user."
            },
            "return_type": "none"
        }
    ]])
)

agent = MonkeyPatch.get_agent(system_prompt=SYSTEM_PROMPT)
while True:
    user_input = input("Enter your command: ")
    llm_output, parsed_action, metadata = MonkeyPatch.step_agent(agent, user_input)
    print(f"Thought: {llm_output}")

    if parsed_action.tool_name:
        getattr(SimpleChatTools, parsed_action.tool_name)(**parsed_action.arguments)

