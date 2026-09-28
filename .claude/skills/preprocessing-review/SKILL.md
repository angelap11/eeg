---
name: preprocessing-review
description: Perform a scoped technical and scientific review of the current EEG preprocessing implementation without expanding beyond the user's requested task.
disable-model-invocation: true
---

# Preprocessing Review

Use this skill during Preprocessing V1.

The user's explicit request determines the scope.

Do not automatically perform a full preprocessing audit unless the user explicitly asks for one.

---

## Scope policy

If the user asks about one problem:

inspect that problem first.

Inspect additional preprocessing stages only when they are required to correctly reason about the requested issue.

Do not use this skill as permission to:

- redesign the pipeline
- implement downstream models
- refactor unrelated code
- solve additional discovered problems
- alter established project decisions

---

## Review order

For a full preprocessing audit, evaluate:

1. EDF loading
2. metadata extraction
3. channel names
4. channel typing
5. EEG-only channel selection
6. sampling-frequency handling
7. filter design
8. Nyquist compatibility
9. NumPy conversion
10. epoch construction
11. epoch temporal ordering
12. recording boundaries
13. subject boundaries
14. NaN/Inf handling
15. shape validation
16. metadata preservation/loss
17. dataset / recording identity preservation
18. cross-dataset leakage risks
19. stationarity diagnostics
20. feature-extraction assumptions
21. downstream forecasting compatibility

For a scoped task, inspect only the relevant subset.

---

## Cross-dataset safeguard

Preprocessing must preserve dataset, recording, subject where available, and temporal identity sufficiently for later cross-dataset evaluation.

Treat random mixing of epochs from REST, SLEEP, and CHB before dataset-level evaluation as a methodological warning.

Do not choose the final train/validation/test dataset assignment unless explicitly requested.

---

## Stationarity safeguard

Stationarity analysis is a REQUIRED project diagnostic.

When the relevant time series representation is available, verify that the project includes:

- rolling mean
- rolling standard deviation
- ADF test

Perform and interpret these diagnostics at an appropriate recording/dataset level.

Do not interpret ADF mechanically.

Distinguish between:
- detecting non-stationarity
- explaining its forecasting implications
- deciding whether a transformation is actually appropriate

Do not automatically force EEG-derived data to become stationary.

---

## Finding classification

Classify every important finding as one of:

### BUG

The implementation is objectively incorrect or behaves incorrectly.

### REQUIRED

Not necessarily a coding bug, but must be resolved for scientifically trustworthy Preprocessing V1.

### OPTIONAL

A reasonable improvement that is not required for Preprocessing V1.

### LATER

Belongs to feature engineering, modelling, evaluation, or another future milestone.

Do not implement OPTIONAL or LATER findings unless explicitly requested.

---

## Evidence classification

When uncertainty matters, distinguish:

### VERIFIED

Confirmed from repository/data/runtime evidence.

### USER-STATED

Explicitly provided by the user but not independently verified.

### INFERRED

Reasoned from available evidence but not directly confirmed.

Do not present INFERRED conclusions as VERIFIED.

---

## Modification procedure

If the user requested a correction:

1. identify the exact defect
2. explain why it is incorrect
3. identify the smallest affected code unit
4. determine whether dependencies require additional changes
5. explain those dependencies before expanding scope
6. modify only what is necessary
7. preserve correct surrounding behaviour
8. provide verification steps
9. wait for runtime evidence when execution is unavailable

Do not combine unrelated fixes into one change.

---

## Scientific safeguards

Never fabricate missing annotations.

Never create `y_sleep` without legitimate Sleep annotations.

Never reinterpret REST/SLEEP/CHB dataset identity as physiological state labels.

Respect recording boundaries.

Respect subject boundaries.

Account for dataset-specific sampling frequencies.

Do not assume a filter cutoff is valid until checked against the recording's Nyquist frequency.

Do not introduce overlapping epochs without explicit discussion of leakage and target semantics.

---

## Output contract

For a scoped review, respond in this order:

1. What is happening
2. Whether it is actually a problem
3. Why
4. Classification: BUG / REQUIRED / OPTIONAL / LATER
5. Smallest correct action
6. Code only if modification was requested
7. What runtime evidence should confirm success

Do not bury the conclusion beneath general EEG theory.

For a full audit, group findings by preprocessing stage and prioritize REQUIRED/BUG findings first.

---

## Stop condition

Stop when the user's requested preprocessing task is resolved.

Do not automatically proceed to:

- the next notebook cell
- the next preprocessing defect
- feature engineering
- state modelling
- transition prediction
- model training

Wait for explicit instruction.