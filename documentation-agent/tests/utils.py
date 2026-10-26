from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ToolCall:
    name: str
    args: Dict[str, Any]


def collect_tools(messages):
    tool_calls = []

    for m in messages:
        for p in m.parts:
            part_kind = p.part_kind

            if part_kind != 'tool-call':
                continue

            # final_result is PydanticAI's structured-output tool, not one of our tools
            if p.tool_name == 'final_result':
                continue

            tool_calls.append(ToolCall(p.tool_name, p.args))

    return tool_calls
