# 02. Q&A Loop and an Agent Library Practice

This chapter focuses on the **outer Q&A loop** and the move from loose functions into an `Agent` class. The visual summary explains that the outer loop repeatedly asks for user input, runs the inner agentic loop, displays the answer, and then returns to the user for the next question. [file:342]

## Learn

### Core idea

The two-loop structure works like this:

- The **inner loop** handles tool usage for one question.
- The **outer loop** handles repeated interaction across many user questions. [file:342]

### Two-loop diagram

```text
OUTER LOOP
ask user for input
    |
    +--> if user says stop -> exit
    |
    +--> append user message to history
                |
                v
          INNER LOOP
          call model
              |
              +--> if tool call -> execute tool -> append result -> repeat
              |
              +--> if final answer -> break inner loop
                |
                v
        return to OUTER LOOP
```

### Why the Agent class matters

The chapter explains that using a class helps by encapsulating agent state and behavior, improving reuse, testing, and maintainability. In that class design, `__init__` stores configuration, `make_call` handles tool execution, `loop` runs the inner loop, and `qna` runs the outer loop. [file:342]

## Quick recap questions

1. Why is one loop not enough for an interactive assistant?  
2. What is the difference between `loop(...)` and `qna()`?  
3. Why does `loop(...)` return `message_history`?  
4. What problem does a class solve compared with putting everything in global scope?  
5. Why is `self.make_call(...)` needed inside the class version?  

## Quiz

### Multiple choice

1. What does the outer loop mainly do?
- A. It routes tool schemas
- B. It manages user interaction across multiple questions
- C. It creates the searchable index
- D. It converts JSON to dicts

2. In the class-based version, which method corresponds to the inner tool-call loop?
- A. `__init__`
- B. `make_call`
- C. `loop`
- D. `qna`

3. In the class-based version, which method corresponds to the outer Q&A loop?
- A. `__init__`
- B. `make_call`
- C. `loop`
- D. `qna`

4. Why is returning `message_history` from `loop(...)` useful?
- A. It lets later turns continue the same conversation state
- B. It reduces token usage to zero
- C. It removes the need for tools
- D. It makes the model deterministic

### Short answer

5. Why does the outer loop usually contain `input('You:')`?  
6. What would happen if the inner loop never broke?  
7. Why is an `Agent` object easier to test than a loose script?  

## Practice

### Practice 1: Convert script to class

Take this responsibility list and map each one to a method:
- store model and prompt,
- execute tool call,
- handle one question,
- handle repeated user questions.

Then write a short explanation for why each belongs there.

### Practice 2: State tracing

Imagine this conversation:

1. User asks: “How do I create a dashboard?”
2. The agent answers.
3. User asks: “Show me the code.”

Explain:
- what the outer loop does at each step,
- what the inner loop does at each step,
- and why the second question can reuse previous context.

### Practice 3: Class vs global script

Make a two-column comparison:
- global-script version,
- `Agent` class version.

Compare them on:
- reuse,
- testing,
- readability,
- extensibility.

## Debug lab

### Bug 1: Wrong call inside class

Suppose you are inside the class version and write:

```python
tool_call_output = make_call(message)
```

instead of:

```python
tool_call_output = self.make_call(message)
```

Why can that fail? What is Python looking for in each case?

### Bug 2: Conversation resets every time

Suppose inside `qna()` you accidentally recreate `message_history` inside the loop each time a new question comes in.

What would the user notice? Why would that defeat the purpose of conversation memory?

### Bug 3: Inner and outer loop confusion

A student says:

> “The outer loop is what executes search() several times.”

Explain why that is incorrect and what the inner loop is responsible for instead.

## Challenge

### Challenge 1: Add max questions

Extend the design conceptually so the outer loop stops after 5 user prompts, even if the user never types `stop`.

Describe:
- which variable you would add,
- where you would increment it,
- where you would check it.

### Challenge 2: Add another agent

Design a second `Agent` instance with different instructions, such as one that summarizes docs instead of answering detailed questions.

Write down:
- what stays the same,
- what changes,
- and why the class structure makes this easy.

## Reflection

1. Can you explain the difference between inner loop and outer loop without looking at notes?  
2. Do you understand why `message_history` must survive across outer-loop turns?  
3. Could you now build a tiny `Agent` class from memory?  

## Self-check answers

### Multiple choice

1. B [file:342]
2. C [file:342]
3. D [file:342]
4. A [file:342]

### Short answer guidance

5. Because it collects new user input for each conversation turn. [file:342]
6. The agent would keep making model/tool iterations for one question and never return control to the user. [file:342]
7. Because its state and behavior are grouped into one object, making isolated tests easier. [file:342]
