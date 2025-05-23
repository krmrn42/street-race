## Collab

It's tedious to wait while the task is complete. So it has to allow working in a branch.
Every process will create its own branch to work on. In a docker maybe?

Retryable errors vs Retry on other errors (just send an empty message).

## Coding process

The process is actually not as straightforward:

1. Get requirements
2. Understand the codebase
   - separate workflow that reads MD and front matter, and creates a summary as related to the requirements
3. Understand requirements given the codebase
4. Create a new branch
5. Ideate on implementation approaches -> save in a doc
6. Choose the best implementation -> save in a doc, commit changes
7. Implement several critical tests in TDD way, commit changes
8. Implement the change, commit changes
   - with every file changed, maintain its front matter
   - maintain read me files for every directory?
9. Iterate on critical tests created before, commit changes
10. Freeze the implementation and create tests for 100% coverage, commit changes
11. Update the docs, commit changes
12. Create a PR

## Tolerant vs. fail-fast code

Models tend to choose tolerant, defensive, forgiving coding style, which is not always right. You need to explain when to go tolerant vs. fail-fast code.

### Tolerant / Defensive / Forgiving\*\*

This approach **tries to make sense of imperfect inputs**, avoid crashing, and preserve uptime and flow even if the data is messy or malformed.

**Traits:**

- Tolerates malformed or unexpected data
- Tries alternate paths or fallbacks
- Warns in logs but doesn’t raise exceptions unless it must
- Aims for resilience over strict correctness

**Pros:**

- Keeps systems running even when upstream components misbehave
- Reduces impact of flaky external systems or data feeds
- Can be better for user-facing systems where downtime is expensive

**Cons:**

- Might silently accept bad data
- Logs can become noisy and harder to act on
- Bugs or data issues might go undetected until much later
- Code paths can become harder to reason about due to hidden assumptions

**Possible labels:**

- _Defensive programming_
- _Forgiving mode_
- _Resilient parser_
- _Fail-soft_

---

### Assertive / Strict / Fail-fast\*\*

This approach **expects well-formed input** and fails loudly and early when things don’t meet expectations.

**Traits:**

- Validates assumptions immediately
- Crashes or throws on unexpected input
- Prefers correctness and traceability over resilience
- Shorter, more explicit code paths

**Pros:**

- Bugs are caught closer to the root cause
- Data integrity is better preserved
- Simpler logic; fewer fallback paths to test
- Encourages upstream systems to be better-behaved

**Cons:**

- Can cause cascading failures if not handled carefully
- Might bring down systems over recoverable edge cases
- Often unsuitable for real-time systems where uptime is critical

**Possible labels:**

- _Fail-fast_
- _Strict mode_
- _Input contract enforcement_
- _Zero-tolerance parser_

---

Always use strongly typed code.

Use coding and design patterns so enforce SOLID principles. TODO: Harvest refactoring guru patterns for specific languages.

Keep all lines unrelated to the current request unchanged.

---

What works:

You:

Describe user story and journey, showing impact and value.

Describe where in codebase this relates to (key file pointers).

Describe own implementation idea.

Stress out key points.

Say: Let's discuss the alternative solutions and trade-offs before coding.

Assistant:

Proposes solutions.

You:

Point out a solution.

Describe what needs to be changed.

Ask to define the necessary interfaces first.

Say: Make sure the created interfaces are syntactically correct.

Assistant:

Creates interfaces.

You (after reviewing code):

Looks good, let's now create tests to describe base scenarios following TDD principles, and align on code structure and data model.

# Static analysis

## Code complexity issues

- C901, Function is too complex (11 > 10)
- PLR0912, line 272: Too many branches (21 > 12)

LLM tries to export individual lines into separate functions, which looks suboptimal. Can we lead to a better solution?

# Scripting

Allow simple scripts inline, find/create a DSL to run things like

```
for x in @src/streetrace/llm: model "
asdfasdf @{x}
"
```

or

```
/cli poetry run ruff... | model "
{_}
summarize
"
```

or

```
/cli poetry run ruff... | model.json "
summarize the output grouping results by file name and listing all issues in each file, like this:
file
   issue, lines 1-2, 3-4: description
   issue, lines 1-2, 3-4: description
provide output as json array, like this:

[
    {
        "file": "path",
        "issues": {
            "code": {
                "description": "...",
                "lines": ["1-2", "3", ...]
            }
        }
    }
]

include only the json array in the output.
" | map(x) | model "
act {x}
" | join | model "summarize" // only this output gets saved in the history of this conversation
```

Get inspiration from the existing LLM shells.

# Context window management

Give LLM a tool to manage its context window. I.e., if the context grows, use these tools to manage the
conversation length: ...

# Tests

All tests should follow Arrange - Act - Assert pattern
Don't mock modules globally

# Human-in-the-loop

Ask human to accept / reject with comment every changed file (or significantly changed file). The workflow becomes more manual, but more engaging. Like - let's try this, here is why - no, I don't like it, think about this - ah, right, how about this?

What am I doing:

I've just added litellm. The issue is that gemini is either extremely slow or not working. We can workaround via https://docs.litellm.ai/docs/providers/custom_llm_server.

# Tools

## list_directory

This is dumb, really. We need to give the model a glob search with a way to search in files as well as file names.
Results should be listed with full relative paths. E.g.:

find_in_files: - path (glob): recursive, wildcards for directories and file names - pattern (regex): search in files

# Contest

The cornerstone of this is letting model know where and how a certain function is implemented. For example, when we say "make this do that" - how does the model know where is the "this"?

The model can explore the codebase, wasting a lot of context pointlessly. Ideally, it needs a way to search for context.

# logprobs

Experiment with using n > 1 and using logprobs / second opinion to find a better response.

# User Advocate

A user advocate agent that can review deliverables.
