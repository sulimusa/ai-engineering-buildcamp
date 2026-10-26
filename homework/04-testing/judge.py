from pydantic import BaseModel, Field
from pydantic_ai import Agent


# The judge's verdict for ONE criterion.
class CriterionCheck(BaseModel):
    criterion: str = Field(description="The criterion text, copied exactly")
    justification: str = Field(description="One or two sentences explaining the decision")
    passed: bool = Field(description="True only if the criterion is clearly satisfied")


# The judge's full answer: one check per criterion, in the same order as the criteria.
class JudgeResult(BaseModel):
    checks: list[CriterionCheck]
    summary: str = Field(description="One sentence overall summary")


JUDGE_INSTRUCTIONS = """
You are a strict evaluator of an AI agent's answer.
You receive a question, the agent's output, and a numbered list of criteria.
Return exactly one check per criterion, in the same order, copying each criterion text.
Mark passed=true only if the criterion is clearly satisfied by the output shown.
Judge only what is in the output. Do not assume or add facts.
""".strip()

# A separate agent, so the judge does not share tools or instructions with the agent under test.
judge_agent = Agent(
    "openai:gpt-4o-mini",
    output_type=JudgeResult,
    instructions=JUDGE_INSTRUCTIONS,
)


def evaluate_agent_performance(criteria: list[str], question: str, output) -> JudgeResult:
    """Ask the judge to grade the agent's output against natural-language criteria."""
    # Number the criteria so the judge can answer one check per line.
    numbered = "\n".join(f"{i}. {criterion}" for i, criterion in enumerate(criteria, start=1))
    # Show the judge the question and everything the agent returned (a pydantic model dumps to JSON).
    prompt = f"""
Question asked to the agent:
{question}

Agent output:
{output.model_dump_json(indent=2)}

Criteria:
{numbered}
""".strip()
    # run_sync runs the judge and waits for its structured verdict.
    return judge_agent.run_sync(prompt).output


def assert_criteria(evaluation: JudgeResult, criteria: list[str]) -> None:
    """Fail with a readable message unless every criterion was checked and passed."""
    # The judge must return exactly one check per criterion.
    assert len(evaluation.checks) == len(criteria), (
        f"Judge returned {len(evaluation.checks)} checks for {len(criteria)} criteria"
    )
    # Collect every failed check so one failure message shows them all.
    failed = [check for check in evaluation.checks if not check.passed]
    details = "\n".join(f"- {check.criterion}\n  why: {check.justification}" for check in failed)
    assert not failed, f"{len(failed)} criteria failed:\n{details}"
