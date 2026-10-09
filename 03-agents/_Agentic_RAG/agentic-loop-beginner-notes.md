# Agent Loop Beginner Notes

This note adds a beginner-friendly mental model to the visual summary of the agent basics section. It is meant to make the **agentic loop** easier to understand before moving on to frameworks. [cite:322]

## Agent mental model

A beginner-friendly way to think about an agent is:

- The **LLM** is the decision-maker.
- Python is the worker.
- **Tools** are the actions Python can perform.
- **message_history** is the running notebook of everything that happened.

An agent has four core components: the LLM, instructions, tools, and memory (`message_history`). The LLM decides whether to call a tool or provide an answer, while the instructions guide behavior and the memory keeps context from prior steps. [file:342]

## The key distinction

The most important thing for a new learner is to separate these two ideas:

- The LLM **decides** what should happen next.
- Python **executes** the real tool function.

The model does not directly run `search()` or `add_entry()`. Instead, it asks for a tool call, your Python loop detects that request, runs the actual function, stores the result in `message_history`, and sends the updated history back to the LLM. This is the core mechanic of the inner tool-call loop. [file:342]

## Inner loop diagram

```text
User asks a question
        |
        v
message_history
(system instructions + user question + prior events)
        |
        v
LLM decides:
"Do I need a tool?"
        |
   +----+----+
   |         |
  Yes        No
   |         |
   v         v
Requests    Produces final
a tool      answer
   |
   v
Python runs the real function
search(...) or add_entry(...)
   |
   v
Tool result is appended to message_history
   |
   +--------> LLM sees the result and decides again
```

The tool-call loop works like this: the LLM receives the current message history, chooses whether to call a tool or provide a final answer, and if it calls a tool the result is added to history and the process repeats. The loop exits only when the LLM provides the final answer instead of another tool call. [file:342]

## One-turn trace

A concrete example often makes the loop easier to understand:

```text
User: "How do I create a dashboard?"

Run 1
LLM: "I need documentation first."
LLM requests: search("create dashboard")
Python executes: search(...)
Python saves: 5 documentation chunks

Run 2
LLM reads the 5 chunks.
LLM requests: search("dashboard panels")

Run 3
LLM reads all gathered results.
LLM returns: final answer
Python sees no tool request -> exits inner loop
```

The lesson explains that the LLM can search again if it is unsure, or answer if it has enough information. That flexibility is what makes the agentic approach different from a fixed sequence. [file:342]

## Traditional RAG vs agentic RAG

Traditional RAG follows a fixed pattern: user query, embedding/search, then answer generation. The LLM does not control the search process in that setup. [file:342]

Agentic RAG gives the LLM more autonomy: it chooses what to search, analyzes the results, decides whether to search again, and only answers when it is satisfied. This means there can be multiple iterations instead of a single search-answer cycle. [file:342]

| Approach | Search control | Typical flow |
|---|---|---|
| Traditional RAG | Fixed pipeline | Query -> search -> answer [file:342] |
| Agentic RAG | LLM-controlled | Query -> LLM decides searches -> maybe more searches -> answer [file:342] |

## Two loops

The lesson also introduces an outer loop around the inner tool-call loop.

```text
Outer Q&A loop:
User asks question -> agent answers -> user asks next question

Inner tool-call loop:
LLM decides -> tool runs -> result returns -> LLM decides again
```

The outer Q&A loop asks for user input, runs the agentic loop to produce an answer, displays the answer, and then waits for the next question. Because the outer loop preserves conversation history, the agent can reference earlier exchanges across multiple turns. [file:342]

## Beginner checks

A new learner should be able to answer these questions after reading this note:

1. Who decides whether a tool is needed? The LLM. [file:342]
2. Who actually runs `search()` or `add_entry()`? Python code in the tool-execution layer. [file:342]
3. Where are tool results stored? In `message_history`, so the LLM can use them next. [file:342]
4. When does the inner loop stop? When the model returns no more `function_call` requests and gives the final answer. [file:342]
5. Why is this agentic? Because the LLM controls whether, what, and how often to search. [file:342]

## Useful production habit

One practical addition for new learners is this rule:

```text
Real agents need safety limits:
- maximum number of iterations,
- timeouts,
- error handling,
- tool permissions,
- logging.
```

The visual summary focuses on fundamentals, but real-world agents benefit from loop guards and observability so they do not get stuck repeating tool calls or silently failing. That production mindset becomes especially useful when moving from a learning notebook to a real application. [file:342]
