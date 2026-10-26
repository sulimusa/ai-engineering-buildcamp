import sys

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from sql_tools import SQLTools, con, setup_database


# The structured answer the agent must return (its output type).
class SQLResult(BaseModel):
    sql_query: str = Field(description="The final SQL query that produced the answer")
    result_text: str = Field(description="The query result, or the answer, as plain text")
    row_count: int = Field(description="How many rows the query returned")


# The agent's rules. The first rule is the one the homework asks for.
INSTRUCTIONS = """
You answer questions about NYC yellow taxi trips stored in a DuckDB table called trips.

ALWAYS start by calling get_schema to see the real column names and types.
Only then write SQL and run it with run_sql. Never guess column names.
Use only read-only queries. If a query fails, read the error, fix the SQL and try again.
Return the final SQL you ran, the result as text, and how many rows it returned.
""".strip()

# Create the tools object once; its methods are what the agent can call.
sql_tools = SQLTools(con)

# The agent: model, structured output type, instructions, and the two tools passed as a list of methods.
agent = Agent(
    "openai:gpt-4o-mini",
    output_type=SQLResult,
    instructions=INSTRUCTIONS,
    tools=[sql_tools.get_schema, sql_tools.run_sql],
)

QUESTION = "What's the average trip distance for rides with 2 passengers?"


# Print the tool calls in order, so we can check the agent started with get_schema.
def print_tool_calls(messages):
    for message in messages:
        for part in message.parts:
            if part.part_kind == "tool-call" and part.tool_name != "final_result":
                print(f"TOOL CALL: {part.tool_name}({part.args})")


if __name__ == "__main__":
    # Make sure the trips table exists (downloads the parquet file once, then reuses it).
    setup_database()
    # Take the question from the command line, or use the homework question.
    question = sys.argv[1] if len(sys.argv) > 1 else QUESTION
    # run_sync runs the whole tool loop and waits for the final structured answer.
    result = agent.run_sync(question)
    print_tool_calls(result.all_messages())
    print(result.output)
