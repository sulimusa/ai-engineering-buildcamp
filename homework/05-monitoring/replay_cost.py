import os
import sys
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from logfire.query_client import LogfireQueryClient

load_dotenv()
read_token = os.getenv("LOGFIRE_READ_TOKEN")
if not read_token:
    raise SystemExit("Add LOGFIRE_READ_TOKEN to homework/05-monitoring/.env first.")

MODEL_PRICES = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
}


def calculate_cost(model_name, input_tokens, output_tokens):
    prices = MODEL_PRICES[model_name.lower()]
    input_cost = (input_tokens / 1_000_000) * prices["input"]
    output_cost = (output_tokens / 1_000_000) * prices["output"]
    return input_cost + output_cost


client = LogfireQueryClient(read_token=read_token)
since = datetime.now(timezone.utc) - timedelta(days=1)

# Use the trace id from the command line, otherwise the newest trivia_session.
if len(sys.argv) > 1:
    trace_id = sys.argv[1]
else:
    sessions = client.query_json_rows(
        sql="SELECT trace_id FROM records WHERE span_name = 'trivia_session' ORDER BY start_timestamp DESC LIMIT 1",
        min_timestamp=since,
    )["rows"]
    trace_id = sessions[0]["trace_id"]

# Every agent run in the trace: the span is "invoke_agent <name>" (older versions used "agent run").
spans = client.query_json_rows(
    sql=f"""
        SELECT span_name, attributes
        FROM records
        WHERE trace_id = '{trace_id}'
          AND (span_name LIKE 'invoke_agent %' OR span_name = 'agent run')
        ORDER BY start_timestamp
    """,
    min_timestamp=since,
)["rows"]


def tokens(attributes, kind):
    # Newer versions report totals under "aggregated_usage"; older ones under "usage".
    for key in (f"gen_ai.aggregated_usage.{kind}_tokens", f"gen_ai.usage.{kind}_tokens"):
        if key in attributes:
            return attributes[key]
    return 0


# Sum over EVERY matching span, not just the latest one.
input_tokens = output_tokens = 0
for number, span in enumerate(spans, start=1):
    i, o = tokens(span["attributes"], "input"), tokens(span["attributes"], "output")
    input_tokens += i
    output_tokens += o
    print(f"run {number}: input={i} output={o}")

print(f"\ntrace_id: {trace_id}")
print(f"agent runs: {len(spans)} | input tokens: {input_tokens} | output tokens: {output_tokens}")
print(f"approximate total cost: ${calculate_cost('gpt-4o-mini', input_tokens, output_tokens):.6f}")
