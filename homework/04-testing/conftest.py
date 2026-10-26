from patch_agent import patch_agent, tracker


def pytest_configure(config):
    # Start tracking before any test runs.
    patch_agent()


def pytest_terminal_summary(terminalreporter):
    # Print the totals at the end of the test run.
    terminalreporter.write_sep("-", "LLM cost summary")
    terminalreporter.write_line(f"agent runs:    {tracker.runs}")
    terminalreporter.write_line(f"input tokens:  {tracker.input_tokens:,}")
    terminalreporter.write_line(f"output tokens: {tracker.output_tokens:,}")
    terminalreporter.write_line(f"total cost:    ${tracker.cost:.6f}")
    if tracker.unpriced:
        terminalreporter.write_line(f"({tracker.unpriced} responses could not be priced)")
