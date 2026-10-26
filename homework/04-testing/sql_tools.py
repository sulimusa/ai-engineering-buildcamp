import os
import urllib.request

import duckdb
from pydantic_ai import ModelRetry

DATA_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
PARQUET_FILE = "yellow_tripdata_2024-01.parquet"

con = duckdb.connect("taxi.db")


def setup_database():
    """Download the parquet file and load it into DuckDB."""
    if not os.path.exists(PARQUET_FILE):
        print(f"Downloading {DATA_URL}...")
        urllib.request.urlretrieve(DATA_URL, PARQUET_FILE)

    con.execute(f"""
        CREATE TABLE IF NOT EXISTS trips AS
        SELECT * FROM '{PARQUET_FILE}'
    """)
    count = con.execute("SELECT COUNT(*) FROM trips").fetchone()[0]
    print(f"Loaded {count} rows")
    return count


# Only these statement types may be run by the agent (a first guard, not real security).
ALLOWED_STATEMENTS = ("select", "with", "describe", "show", "explain")
# The most rows run_sql returns, so a huge result cannot flood the model's context.
MAX_ROWS = 50


# Group the two database tools in a class, like SearchTools in the module.
class SQLTools:
    # Receive the database connection instead of creating it here, so tests can pass a different one.
    def __init__(self, con):
        self.con = con  # The DuckDB connection both tools use.

    # The docstring and type hints are what the model sees as this tool's description.
    def get_schema(self) -> str:
        """Return every column of the trips table with its type. Call this before writing SQL."""
        # DESCRIBE returns one row per column: (column_name, column_type, null, key, default, extra).
        rows = self.con.execute("DESCRIBE trips").fetchall()
        # Keep only the name and the type, one "name: type" line per column.
        return "\n".join(f"{row[0]}: {row[1]}" for row in rows)

    def run_sql(self, query: str) -> str:
        """Run a read-only SQL query on the trips table. Returns column headers and up to 50 rows as text."""
        # Reject anything that is not a read-only statement. ModelRetry sends this message back to the model.
        first_word = query.strip().split(None, 1)[0].lower() if query.strip() else ""
        if first_word not in ALLOWED_STATEMENTS:
            raise ModelRetry(f"Only read-only queries are allowed ({', '.join(ALLOWED_STATEMENTS)}). Rewrite the query.")
        try:
            result = self.con.execute(query)
        except duckdb.Error as error:
            # A wrong column name or bad syntax is something the model can fix, so let it retry.
            raise ModelRetry(f"SQL error: {error}. Check the column names with get_schema and try again.")
        # result.description lists the columns; the first item of each entry is the column name.
        headers = [column[0] for column in result.description]
        # Fetch at most MAX_ROWS rows, even if the query matches millions.
        rows = result.fetchmany(MAX_ROWS)
        # Build text: a header line, then one line per row, with values separated by " | ".
        lines = [" | ".join(headers)]
        lines += [" | ".join(str(value) for value in row) for row in rows]
        return "\n".join(lines)
