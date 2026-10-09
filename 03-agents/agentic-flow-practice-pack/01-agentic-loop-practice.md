# 01. Agentic Loop Practice

This chapter focuses on the **inner tool-call loop**. The visual summary explains that the loop works by giving the LLM the current message history, letting it decide whether to call a tool or answer, repeating when tools are used, and exiting when a final answer is produced. [file:342]

## Learn

### Core idea

The agentic loop is the repeated cycle where:

1. The LLM reads the current `message_history`.
2. The LLM decides whether it needs a tool.
3. If it requests a tool, Python executes the real function.
4. The tool result is appended to `message_history`.
5. The LLM sees the updated history and decides again.
6. The loop ends only when the LLM gives an answer instead of another tool call. [file:342]

### Mental model

```text
LLM = decision-maker
Python = executor
Tools = actions Python can perform
message_history = the running memory of the conversation
```

### Dependency diagram

```text
response = client.responses.create(...)
        |
        v
response.output
        |
        +--> message item -> print assistant text
        |
        +--> function_call item
                  |
                  v
             make_call(message)
                  |
                  +--> if name == "search" -> search(**arguments)
                  |
                  +--> if name == "add_entry" -> add_entry(**arguments)
                  |
                  v
       function_call_output appended to message_history
                  |
                  v
         next model iteration can read the result
```

## Quick recap questions

Answer these in 1-2 sentences each.

1. Why is the loop called “agentic”?  
2. What is the difference between `response.output` and `tool_call_output`?  
3. Why does the loop need `message_history.extend(response.output)` before executing tools?  
4. Who decides whether a tool is needed: the LLM or Python?  
5. Who actually runs `search(...)`: the LLM or Python?  

## Quiz

### Multiple choice

1. What stops the inner loop?
- A. When `iteration_number == 3`
- B. When `message_history` reaches 10 items
- C. When no function calls are found in the current response
- D. When the search tool returns no results

2. What is the main job of `make_call(message)`?
- A. It asks the user for the next question
- B. It converts tool requests into real Python function execution
- C. It prints the final answer only
- D. It creates the OpenAI client

3. Which statement is true?
- A. The tool schema itself executes Python code
- B. `search_tool` directly searches the index
- C. The model can directly call Python functions without your code
- D. Python must inspect the model output and run the actual function

4. Why is `message_history` important?
- A. It stores only user messages
- B. It is how the model remembers prior steps and tool results
- C. It stores only the final answer
- D. It replaces the tools list

### Short answer

5. Why would a second search sometimes be necessary after the first one?  
6. What would happen if you forgot to append `tool_call_output` to `message_history`?  
7. Why is a typo in a tool name a serious issue?  

## Practice

### Practice 1: Trace the loop

Take this pseudocode and annotate what changes after each step:

```python
response = client.responses.create(...)
message_history.extend(response.output)
for message in response.output:
    if message.type == 'function_call':
        tool_call_output = make_call(message)
        message_history.append(tool_call_output)
```

Write down:
- what exists before the response,
- what gets added by `extend`,
- what gets added by `append`,
- and what the model can see in the next iteration.

### Practice 2: Mini rebuild

Write a tiny version of `make_call(...)` that supports only one tool, `search`. Then answer:
- what input shape it expects,
- what output shape it must return,
- and why `call_id` matters.

### Practice 3: Explain like a teacher

Explain this sentence in plain English:

> “The LLM chooses the next action, but Python executes the action.”

Use a 4-6 line explanation with one concrete example.

## Debug lab

### Bug 1: Missing function

You run the loop and get:

```text
NameError: name 'make_call' is not defined
```

Answer:
1. Why does this happen?  
2. What cell probably was not run?  
3. How can you verify whether `make_call` exists right now?  

### Bug 2: The loop never becomes useful

Imagine you forgot this line:

```python
message_history.append(tool_call_output)
```

What would the next iteration be missing? Why would the model be more likely to repeat the same search or fail to progress?

### Bug 3: Wrong tool name

Suppose the schema says:

```python
'name': 'add_entry'
```

but `make_call(...)` checks for:

```python
elif name == 'store_entry':
```

What happens and why?

## Challenge

### Challenge 1: Add a safety guard

Modify the loop design so it cannot run forever. Add a `max_iterations` variable and explain:
- where the check should go,
- what should happen when the max is reached,
- and why this matters in real agents.

### Challenge 2: Add a new tool

Design a third tool named `list_titles()` that returns the titles of the first 10 docs in the index.

Write:
- the Python function signature,
- the tool schema,
- and the `make_call(...)` branch needed to support it.

## Reflection

Answer in your own words:

1. What part of the agentic loop is still hardest for you?  
2. Can you now clearly separate tool metadata from the real Python function?  
3. Could you explain the agentic loop on a whiteboard without notes?  

## Self-check answers

### Multiple choice

1. C [file:342]
2. B [file:342]
3. D [file:342]
4. B [file:342]

### Short answer guidance

5. Because the first search may be incomplete or too broad, and the LLM can refine its search once it sees the initial results. [file:342]
6. The model would not see the tool result in the next turn, so it would lose the benefit of the tool call. [file:342]
7. Because the model may request one tool name, while Python routes only another; then the real function will not be executed correctly. [cite:322]
