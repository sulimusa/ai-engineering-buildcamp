from decimal import Decimal

from pydantic_ai.agent.abstract import AbstractAgent


# Collects token counts and cost from every agent run made while the tests execute.
class CostTracker:
    def __init__(self):
        self.runs = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.cost = Decimal(0)
        self.unpriced = 0  # model responses whose price could not be looked up

    def record(self, result):
        self.runs += 1
        # new_messages() holds only this run's messages, so history is not counted twice.
        for message in result.new_messages():
            if message.kind != "response":
                continue
            self.input_tokens += message.usage.input_tokens
            self.output_tokens += message.usage.output_tokens
            try:
                # cost() looks the model up in PydanticAI's price table.
                self.cost += message.cost().total_price
            except LookupError:
                self.unpriced += 1


tracker = CostTracker()


def patch_agent():
    """Wrap Agent.run so every run, including the judge's, is recorded. Safe to call twice."""
    original = AbstractAgent.run
    if getattr(original, "_cost_tracked", False):
        return

    # run_sync calls run internally, so patching run covers both.
    async def tracked_run(self, *args, **kwargs):
        result = await original(self, *args, **kwargs)
        tracker.record(result)
        return result

    tracked_run._cost_tracked = True
    AbstractAgent.run = tracked_run
