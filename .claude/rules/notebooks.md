---
paths:
  - "**/*.ipynb"
---

# Notebook Working Rules

## Incremental understanding

On first encounter with a notebook, inspect enough of its structure to understand the relevant data flow.

After that, reuse the established understanding unless:

- relevant cells changed
- dependencies are unclear
- runtime evidence contradicts prior understanding
- execution-order or hidden-state problems are suspected

Do not re-read or re-analyze the entire notebook for every correction.

For each task, begin with:

1. the target cell/function
2. its required upstream dependencies
3. its immediately relevant downstream consumers

Expand beyond these only when necessary.

---

## Notebook state

Do not assume notebook state that is not visible.

Distinguish between:

- code present in the notebook
- cells that have actually been executed
- outputs that were actually produced
- values that are only assumed to exist

Executed outputs supplied by the user are runtime evidence.

Remember that notebooks may contain stale state from previous executions.

When relevant, reason about whether the notebook would survive:

Restart Kernel -> Run All

---

## Editing rules

A request to inspect or explain a cell does not authorize changing it.

A request to modify one cell does not authorize changing neighboring cells unless the target change cannot function correctly without them.

If another cell must change:

1. explain why
2. identify it explicitly
3. keep the additional change minimal

Do not perform notebook-wide cleanup or refactoring unless requested.

Preserve chronological data dependencies.

---

## Corrections

When replacement code is appropriate:

- identify the exact target cell/function
- preserve surrounding interfaces
- return the complete replacement for the affected logical unit
- do not rewrite unrelated notebook code

Do not claim an execution problem is resolved until there is runtime evidence.

---

## Inspection escalation

If the local cell cannot be understood without tracing a variable or function:

trace only that dependency.

If the dependency chain reveals a broader architectural issue:

report the issue before expanding the scope of the requested change.

Broad notebook inspection is a fallback, not the default.