import sys

import logfire
from dotenv import load_dotenv
from pydantic_ai import Agent

from trivia_tools import TriviaTools

# Read LOGFIRE_TOKEN (and OPENAI_API_KEY, if you keep it there) from a .env file next to this script.
load_dotenv()
# Send traces to Logfire only when a token is present, so the script still runs without one.
logfire.configure(send_to_logfire="if-token-present")
# Record every agent run, model request and tool call as spans.
logfire.instrument_pydantic_ai()

instructions = """You are a trivia quizmaster. When asked to play trivia:
1. Use the available tools to fetch trivia questions
2. Ask the player one question at a time with multiple choice options
3. Wait for their answer before moving to the next question
4. When the player answers, explain why the correct answer is correct - add interesting context and facts
5. After all questions, give the final score
"""

trivia_tools = TriviaTools()

agent = Agent(
    'openai:gpt-4o-mini',
    name='agent',
    tools=[trivia_tools.get_categories, trivia_tools.get_questions],
    instructions=instructions,
)


# Print the tool calls in order, so we can see which tool the agent calls first.
def print_tool_calls(messages):
    for message in messages:
        for part in message.parts:
            if part.part_kind == "tool-call":
                print(f"TOOL CALL: {part.tool_name}({part.args})")


# The interactive conversation loop provided by the homework.
def run(prompt):
    # The conversation so far; passing it back in lets the agent remember earlier turns.
    message_history = []

    while True:
        # Each pass through this loop is ONE separate agent run (one invoke_agent span).
        result = agent.run_sync(prompt, message_history=message_history)
        print(result.output)
        message_history = result.all_messages()

        # Ask the player for their next message; an empty line or "stop" ends the session.
        prompt = input("You (write 'stop' to stop): ")
        if not prompt or prompt.lower().strip() == 'stop':
            break


if __name__ == "__main__":
    # Use the prompt from the command line if given, otherwise the homework's prompt.
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Let's play 5 easy questions from Science & Nature"
    # Group every agent run in the session under one parent span, so Logfire shows them as one trace.
    with logfire.span('trivia_session'):
        run(prompt)
