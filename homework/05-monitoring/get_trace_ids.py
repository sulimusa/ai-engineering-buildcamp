import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from logfire.query_client import LogfireQueryClient

# Read LOGFIRE_READ_TOKEN from the .env file next to this script.
load_dotenv()
read_token = os.getenv("LOGFIRE_READ_TOKEN")
if not read_token:
    raise SystemExit("Add LOGFIRE_READ_TOKEN=<your read token> to homework/05-monitoring/.env first.")

# The query client needs a start of the time window; look back one day.
since = datetime.now(timezone.utc) - timedelta(days=1)

client = LogfireQueryClient(read_token=read_token)

# Every grouped session: one trivia_session span per trace.
sessions = client.query_json_rows(
    sql="""
        SELECT trace_id, start_timestamp, duration
        FROM records
        WHERE span_name = 'trivia_session'
        ORDER BY start_timestamp DESC
    """,
    min_timestamp=since,
)["rows"]

# How many agent runs sit inside each trace (the grouped session should have 6).
runs = client.query_json_rows(
    sql="""
        SELECT trace_id, COUNT(*) AS agent_runs
        FROM records
        WHERE span_name = 'invoke_agent agent'
        GROUP BY trace_id
    """,
    min_timestamp=since,
)["rows"]
runs_per_trace = {row["trace_id"]: row["agent_runs"] for row in runs}

print("trivia_session traces (newest first):")
for row in sessions:
    count = runs_per_trace.get(row["trace_id"], 0)
    print(f"  trace_id={row['trace_id']}  started={row['start_timestamp']}  agent_runs_inside={count}")
if not sessions:
    print("  none found; run the session first, and check the read token belongs to the same project.")
