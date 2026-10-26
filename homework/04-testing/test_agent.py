import re

import pytest

from sql_agent import agent
from sql_tools import con
from judge import CriterionCheck, JudgeResult, assert_criteria, evaluate_agent_performance
from utils import collect_tools

QUESTION = "How many trips had more than 5 passengers?"

# Found by running the query directly in DuckDB first:
#   SELECT COUNT(*) FROM trips WHERE passenger_count > 5
# The January 2024 data never changes, so the exact number is safe to hardcode.
EXPECTED_COUNT = 22413


def test_expected_count_matches_database():
    # Free check (no model call): makes sure the hardcoded number still matches the data.
    count = con.execute("SELECT COUNT(*) FROM trips WHERE passenger_count > 5").fetchone()[0]
    assert count == EXPECTED_COUNT


def test_agent_counts_trips_with_more_than_5_passengers():
    # Real model call (costs a few cents). run_sync runs the whole tool loop and waits for the answer.
    result = agent.run_sync(QUESTION)
    output = result.output

    # The agent must report the SQL it ran, and it must not be empty or blank.
    assert isinstance(output.sql_query, str)
    assert output.sql_query.strip() != ""

    # The model may write 22413 or 22,413, so remove commas before looking for the number.
    assert str(EXPECTED_COUNT) in output.result_text.replace(",", "")


def test_agent_gets_schema_first_then_runs_sql():
    # Real model call (costs a few cents).
    result = agent.run_sync("What is the most common payment type?")

    # Read the recording of the run and keep only our real tool calls, in order.
    tool_calls = collect_tools(result.all_messages())
    print("Tool calls in order:", [call.name for call in tool_calls])

    # The agent must call at least one tool before we index into the list.
    assert len(tool_calls) >= 1
    # The first call must be get_schema, as the instructions require.
    assert tool_calls[0].name == "get_schema"
    # run_sql must also have been called at some point.
    assert "run_sql" in [call.name for call in tool_calls]


def test_assert_criteria_reports_failures():
    # Free check (no model call): assert_criteria must fail and name the failed criterion.
    criteria = ["first", "second"]
    verdict = JudgeResult(
        checks=[
            CriterionCheck(criterion="first", justification="ok", passed=True),
            CriterionCheck(criterion="second", justification="missing", passed=False),
        ],
        summary="one failed",
    )
    try:
        assert_criteria(verdict, criteria)
    except AssertionError as error:
        assert "second" in str(error) and "missing" in str(error)
    else:
        raise AssertionError("assert_criteria should have failed")


def test_judge_highest_average_fare_by_hour():
    question = "Which hour of the day has the highest average fare amount?"
    # Real model calls (the agent, then the judge): a few cents.
    result = agent.run_sync(question)

    criteria = [
        "the SQL query correctly calculates average fare by hour of day",
        "the result identifies a specific hour as having the highest average fare",
        "the result includes the actual average fare amount",
    ]
    evaluation = evaluate_agent_performance(criteria, question, result.output)
    # Show the judge's reasoning when running with -s.
    print(result.output)
    for check in evaluation.checks:
        print(f"{'PASS' if check.passed else 'FAIL'}: {check.criterion} -- {check.justification}")
    assert_criteria(evaluation, criteria)


# ---- Question 6: more tests, one per question -------------------------------------------------
# Expected values were found by running the queries directly in DuckDB (the data never changes).


def ask(question):
    """Run the agent (a real model call) and return its output and the tool names in order."""
    result = agent.run_sync(question)
    tool_names = [call.name for call in collect_tools(result.all_messages())]
    print(f"\nTool calls: {tool_names}\nSQL: {result.output.sql_query}\nResult: {result.output.result_text}")
    return result.output, tool_names


def numbers_in(text):
    """Return every number in the text as a float, so '22,413' and '22413' both count."""
    return [float(n.replace(",", "")) for n in re.findall(r"\d[\d,]*(?:\.\d+)?", text)]


def assert_has_number(text, expected, tolerance=0.0):
    """Fail unless the text contains a number equal to expected (within the tolerance)."""
    found = numbers_in(text)
    assert any(abs(n - expected) <= tolerance for n in found), f"expected ~{expected} in {text!r}, found {found}"


def assert_schema_first_then_sql(tool_names):
    """The behavior every question should show: schema first, then at least one query."""
    assert len(tool_names) >= 1
    assert tool_names[0] == "get_schema"
    assert "run_sql" in tool_names


def test_average_tip_for_credit_card_payments():
    # Scenario: needs the payment_type code for credit card (1) and the tip_amount column.
    output, tools = ask("What is the average tip amount for credit card payments?")
    assert_schema_first_then_sql(tools)
    sql = output.sql_query.lower()
    assert "tip_amount" in sql and "payment_type" in sql
    assert_has_number(output.result_text, 4.17, tolerance=0.01)     # true value 4.1697


def test_pickup_location_with_most_trips():
    # Scenario: group by PULocationID and take the top one (132, with 145,240 trips).
    output, tools = ask("Which pickup location (PULocationID) has the most trips?")
    assert_schema_first_then_sql(tools)
    assert "pulocationid" in output.sql_query.lower()
    assert_has_number(output.result_text, 132)


def test_average_fare_for_trips_longer_than_10_miles():
    # Scenario: a filter on trip_distance and an average of fare_amount.
    output, tools = ask("What is the average fare for trips longer than 10 miles?")
    assert_schema_first_then_sql(tools)
    sql = output.sql_query.lower()
    assert "fare_amount" in sql and "trip_distance" in sql
    assert_has_number(output.result_text, 62.88, tolerance=0.01)    # true value 62.8808


def test_trips_with_zero_passengers():
    # Scenario: filter on the passenger_count column (the answer to the homework question).
    output, tools = ask("How many trips had zero passengers recorded?")
    assert_schema_first_then_sql(tools)
    assert "passenger_count" in output.sql_query.lower()
    assert_has_number(output.result_text, 31465)


def test_busiest_day_of_week():
    # Scenario: derive the weekday from the pickup timestamp; Wednesday has the most trips (495,032).
    output, tools = ask("What is the busiest day of the week for taxi trips?")
    assert_schema_first_then_sql(tools)
    assert "tpep_pickup_datetime" in output.sql_query.lower()
    # The trip count is the specific value, whatever form the day takes.
    assert_has_number(output.result_text, 495032)
    # The agent may say "Wednesday" or give a weekday number (3 when Sunday is 0), so accept either.
    text = output.result_text.lower()
    assert "wednesday" in text or 3 in numbers_in(text)
