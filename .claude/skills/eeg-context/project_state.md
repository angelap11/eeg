# EEG Project State

Last intentionally updated: 2026-09-14 (major completion sprint: RF + TCN + 3-way comparison, see Sections 26-29)

This document describes the **current project state**, not conversational history.

Update existing sections when facts change rather than appending a chronological diary.

The repository, actual notebook, data, and runtime outputs remain the highest source of truth. If this document conflicts with them, report the discrepancy and follow repository/runtime evidence.

---

# 1. PROJECT OBJECTIVE

The project is a research-oriented **dynamic EEG state and transition forecasting system**.

It began as:

```text
EEG
→ feature extraction
→ numerical index
```

but has evolved toward answering:

1. What state is the brain in now?
2. How is that state changing?
3. Is a state transition approaching?
4. Approximately when could it occur?
5. What state is likely to come next?

The long-term conceptual output for time `t` is:

```text
CURRENT STATE
state representation / probabilities

CURRENT DYNAMICS
deviation / instability
trend
trajectory

TRANSITION RISK
within 30 s
within 60 s
within 120 s

LIKELY NEXT STATE
candidate destination probabilities
```

The 30 s / 60 s / 120 s risks should eventually form a **consistent cumulative transition curve**, not three unrelated predictions.

This is the long-term objective.

It is NOT the current implementation state.

---

# 2. CURRENT DATA DOMAINS

The project currently works with three EEG domains:

```text
REST
SLEEP
CHB / seizure EEG
```

They must be treated as distinct domains.

They differ in factors including:

* physiological context
* sampling frequency
* channels
* montage
* recording setup
* subjects
* annotations
* intended use

Dataset identity must never automatically be interpreted as physiological brain state.

Do not concatenate or directly compare these datasets as though they were homogeneous unless the methodology explicitly accounts for domain differences.

## Observed sampling frequencies

Project history reports approximately:

```text
REST  → 160 Hz
SLEEP → 100 Hz
CHB   → 256 Hz
```

These values should be retrieved and validated from actual MNE/EDF metadata rather than recreated as unquestioned constants downstream.

---

# 3. VERIFIED / ESTABLISHED CURRENT FACTS

## 3.1 Existing notebook foundation

The project already contains an EEG analysis pipeline rather than starting from zero.

The existing work includes or has included:

```text
EDF loading with MNE
↓
NumPy conversion
↓
30-second epoching
↓
Welch PSD
↓
band-power extraction
↓
spectral entropy
↓
feature DataFrames
↓
early scaling/index experiments
```

Known concepts/functions from the existing implementation include:

* `mne.io.read_raw_edf(preload=True)`
* `make_epochs(...)`
* `scipy.signal.welch`
* EEG band-power calculation
* spectral entropy
* fixed-duration windows
* feature DataFrames

Correct existing work should be preserved rather than replacing the project wholesale.

---

## 3.2 No verified Sleep hypnogram

There is currently **no verified ground-truth Sleep hypnogram / sleep-stage annotation source** available in the established project state.

Therefore there is currently:

```text
NO legitimate y_sleep
```

and no justified supervised labels for:

```text
Wake
N1
N2
N3
REM
```

Never fabricate these labels.

A commented path, filename, old variable, or previous-agent claim is not evidence that a hypnogram exists.

Until a genuine annotation source is verified, Sleep EEG can still be processed and used for appropriate signal-analysis or unsupervised/state-representation work, but named supervised sleep-stage transition training is not legitimate.

---

## 3.3 Sleep recording channel composition

The Sleep PSG contains multiple physiological signal types, including approximately:

```text
EEG Fpz-Cz
EEG Pz-Oz
EOG horizontal
Resp oro-nasal
EMG submental
Temp rectal
Event marker
```

A major preprocessing problem was discovered:

MNE initially interpreted all seven channels as EEG.

Therefore code equivalent to:

```python
pick_types(eeg=True)
```

could incorrectly select:

```text
EEG
+
EOG
+
respiration
+
EMG
+
temperature
+
event marker
```

rather than only brain EEG channels.

This could contaminate downstream spectral features and channel averaging.

For Sleep, the intended genuine EEG channels are:

```text
EEG Fpz-Cz
EEG Pz-Oz
```

The actual corrected notebook must still be inspected to verify that channel typing and EEG-only selection are implemented correctly.

---

## 3.4 Existing downstream feature mismatch

A previous mismatch existed between produced feature names and names expected later by scaling/index code.

Feature extraction produced names similar to:

```text
std
var
delta
theta
alpha
entropy
```

while downstream code expected names similar to:

```text
theta_power
delta_power
alpha_power
spectral_entropy
```

Project history reports that this mismatch was corrected.

The current notebook remains the authority for whether the correction is actually present.

---

## 3.5 Clean-run problems previously identified

Two notebook execution issues were previously identified and reportedly removed:

* a raw `conda install statsmodels` command embedded in notebook execution
* a stray `dobro aj` line

A final clean-run guarantee has not been assumed merely from this report.

The desired validation remains:

```text
Restart Kernel
→ Run All
→ successful deterministic execution
```

---

# 4. IMPLEMENTATION REPORTED BUT REQUIRING CURRENT NOTEBOOK VERIFICATION

Project history reports that a corrected notebook was produced under the name:

```text
EEG_preprocessing_v1.ipynb
```

Do NOT assume the following merely because this document says they were intended.

Verify them from the actual notebook before relying on them.

## 4.1 Sleep path verification

A previous bug checked:

```text
edf_r01.exists()
```

while supposedly validating the Sleep file.

`edf_r01` belonged to REST.

The intended correction is to check the actual Sleep path variable:

```text
edf_s01
```

---

## 4.2 Sleep channel typing

The intended channel-type mapping is:

```text
EEG Fpz-Cz      → EEG
EEG Pz-Oz       → EEG
EOG horizontal  → EOG
Resp oro-nasal  → RESP
EMG submental   → EMG
Temp rectal     → MISC
Event marker    → STIM
```

After typing, EEG selection should return only the genuine EEG channels.

For the known Sleep recording, expected EEG channel count:

```text
2
```

Verify this against actual notebook output.

---

## 4.3 Common preprocessing function

A preprocessing function conceptually named:

```python
preprocess_eeg(...)
```

was introduced/intended to perform approximately:

```text
MNE Raw
↓
select channels typed as EEG
↓
validate channels
↓
filter
↓
convert to NumPy
↓
finite-value checks
```

Verify its actual signature, behaviour, and existence before referring to it as implemented fact.

---

## 4.4 Processing order

The intended corrected ordering is:

```text
EDF
↓
correct channel types
↓
select EEG
↓
filter
↓
validate
↓
NumPy conversion
```

This replaces the earlier pattern of converting raw EDF content to NumPy too early.

Verify the actual notebook data flow.

---

## 4.5 Filtering

The current intended filtering range is approximately:

```text
0.5–40 Hz
```

Do not accept this blindly across all datasets.

For each recording/dataset verify:

* actual sampling frequency
* Nyquist frequency
* filter validity
* relevant MNE behaviour
* consistency with downstream spectral features

A filter merely executing without error does not prove that the methodological choice is appropriate.

---

# 5. ESTABLISHED PROJECT DECISIONS

These decisions should be treated as deliberate unless explicitly reopened.

## 5.1 Epoch duration

```text
WIN_SEC = 30.0
```

Epoch duration:

```text
30 seconds
```

---

## 5.2 Epoch overlap

```text
OVERLAP = 0.0
```

Current epochs are non-overlapping.

This is deliberate.

The temporal interpretation is:

```text
+1 epoch = +30 s
+2 epochs = +60 s
+4 epochs = +120 s
```

Do not introduce overlap casually.

Any proposed overlap change must first consider:

* temporal leakage
* dependence between samples
* target construction
* transition-horizon semantics
* train/validation/test splitting

---

## 5.3 Epoch representation

`make_epochs(...)` is intended to produce data shaped conceptually as:

```text
(n_epochs, channels, samples_per_epoch)
```

For Sleep at approximately 100 Hz:

```text
30 s × 100 samples/s = 3000 samples/channel/epoch
```

so the intended Sleep representation is approximately:

```text
(n_epochs, 2, 3000)
```

after correct EEG-only selection.

Actual shapes must be verified at runtime.

---

## 5.4 Temporal order

Chronological epoch order must be preserved.

The project is fundamentally temporal, so arbitrary epoch shuffling during preprocessing would destroy information needed for future transition modelling.

Training-time shuffling decisions belong to later modelling design and must respect sequence construction and leakage constraints.

---

## 5.5 Domain separation

REST, SLEEP, and CHB are not interchangeable representations of different brain states.

Differences between them can arise from dataset/domain effects rather than physiology alone.

Cross-dataset normalization, comparison, transfer, or fusion must therefore be methodologically justified.

---

## 5.6 Cross-dataset evaluation requirement

The teaching assistant explicitly recommended evaluating generalization across datasets rather than mixing all EEG time series and randomly splitting them.

The project should therefore preserve REST, SLEEP, and CHB as separate dataset domains throughout preprocessing and later modelling.

Candidate experimental strategies include:

1. train on one dataset, validate on another, test on the third
2. rotate dataset roles across experiments
3. leave-one-dataset-out evaluation

The exact final split strategy is NOT YET ESTABLISHED.

Preprocessing must not destroy the dataset/recording identity needed to perform these experiments later.

## 5.7 Stationarity analysis requirement

The teaching assistant explicitly requested analysis of whether the relevant EEG-derived time series are stationary or non-stationary.

Required exploratory diagnostics include at minimum:

- rolling mean
- rolling standard deviation
- Augmented Dickey-Fuller (ADF) test

These checks should be performed separately on appropriate time series / recordings rather than on a naïvely concatenated REST + SLEEP + CHB signal.

The purpose is to:

1. observe whether statistical properties change over time
2. characterize differences between the EEG domains
3. understand implications for forecasting-model choice and behaviour

A non-stationary result does NOT automatically authorize transforming the signal to force stationarity.

Any differencing, detrending, normalization, or other stationarity-related transformation must be scientifically justified with respect to the forecasting target.

Exact placement of this analysis in the notebook/pipeline should be determined from the actual implementation.

---

# 6. CURRENT MILESTONE

## Preprocessing V1

Status:

```text
IN PROGRESS
```

**2026-09-08 correction (repository/runtime evidence overrides the stale
status below):** despite this section's "IN PROGRESS" status and Section 16
listing TCN training / NSDI-style indices / transition prediction as
"rejected during the current milestone," the repository already contains
completed, executed TCN forecasting work
(`EEG_TCN_seizure_forecasting.ipynb`, `EEG_TCN_state_deviation_forecasting.ipynb`,
saved outputs under `outputs/modeling/tcn_state_deviation_forecasting/`) and,
as of this update, completed binary preictal/interictal labeling
(`EEG_binary_preictal_labeling.ipynb`) built on top of it. See Section 18
for the accurate, current status of all of this work. Preprocessing V1
itself has not been re-audited as part of this update -- only the
forecasting-target work is being reconciled here.

The truthful goal of Preprocessing V1 is:

```text
raw EEG
↓
correct signal typing
↓
EEG-only selection
↓
appropriate filtering
↓
30-second chronological epochs
↓
quality control
↓
trustworthy clean X
```

It does NOT currently include supervised Sleep labels because no verified hypnogram exists.

For Sleep, the desired verified endpoint is approximately:

```text
channels:
EEG Fpz-Cz
EEG Pz-Oz

sampling frequency:
derived from metadata, expected ≈ 100 Hz

filter:
methodologically validated

epoch duration:
30 s

overlap:
0

samples per epoch:
expected ≈ 3000

X shape:
(n_epochs, 2, 3000)

finite values:
yes

temporal order:
preserved

y_sleep:
does not exist
```

---

# 7. PREPROCESSING V1 — REMAINING VERIFICATION / WORK

Before declaring Preprocessing V1 complete, inspect the actual notebook and establish confidence in the following.

## Data loading

* EDF paths are correct.
* Each intended recording actually exists.
* MNE loads the expected recording.
* Sampling frequency comes from metadata.

## Channel handling

* Channel names are inspected.
* Channel types are correct.
* Non-EEG physiological channels are not accidentally treated as EEG.
* EEG selection returns the intended channels.
* Dataset-specific channel differences are understood.

## Filtering

* Filter parameters are valid for each dataset's sampling frequency.
* Nyquist constraints are respected.
* Filtering is applied to appropriate signal channels.
* No scientifically unjustified universal assumption is silently imposed across datasets.

## NumPy conversion

* Conversion occurs after required MNE-level preprocessing.
* Array shapes are known.
* Important metadata lost during NumPy conversion is understood and preserved separately where necessary.

## Epoching

* Epoch duration is exactly 30 seconds.
* Overlap is zero.
* samples-per-epoch matches each dataset's actual sampling frequency.
* chronological ordering is preserved.
* leftover samples are handled intentionally.
* recording boundaries are not crossed accidentally.
* subject boundaries are not crossed accidentally.

## Quality control

At minimum establish:

* expected dimensionality
* expected channel count where known
* expected samples per epoch
* no NaNs
* no infinities
* valid temporal ordering

Add additional QC only where scientifically useful.

## Clean execution

Ultimately verify:

```text
Restart Kernel
→ Run All
```

without reliance on stale hidden state.

---

# 8. FEATURE ENGINEERING — EXISTING FOUNDATION

Feature engineering is NOT the current priority until Preprocessing V1 is trustworthy.

Existing/simple features include approximately:

```text
standard deviation
variance
delta power
theta power
alpha power
spectral entropy
```

Welch PSD is already part of the existing project foundation.

Before expanding features, verify and understand:

* PSD implementation
* `nperseg`
* resulting frequency resolution
* band definitions
* numerical integration method
* absolute versus relative band power
* effect of sampling frequency
* channel aggregation
* normalization

Do not add large arbitrary EEG feature sets merely because they exist.

Every future feature should serve a clear modelling or scientific purpose.

---

# 9. PLANNED FUTURE ARCHITECTURE

Everything in this section is **PLANNED / CONCEPTUAL**, not established implementation.

Do not report any item here as already implemented unless repository evidence confirms it.

The envisioned architecture is approximately:

```text
CONTINUOUS EEG
      ↓
PREPROCESSING
      ↓
30 s EPOCHS
      ↓
┌───────────────┬─────────────────┐
│               │                 │
qEEG FEATURES   RAW EEG ENCODER   │
                later CNN/EEGNet  │
│               │                 │
└───────────────┴─────────────────┘
      ↓
STATE REPRESENTATION
      ↓
STATE GEOMETRY
      ↓
DEVIATION / INSTABILITY TRAJECTORY
      ↓
TEMPORAL MODEL
      ↓
TCN
      ↓
TRANSITION PREDICTION
      ↓
30 s / 60 s / 120 s
      ↓
TRANSITION CURVE
```

The currently preferred future temporal model is a:

```text
TCN — Temporal Convolutional Network
```

Possible later comparisons may include:

* GRU/LSTM
* MLP
* ARIMA
* Chronos-2
* possibly Transformers

None of these should be implemented prematurely during Preprocessing V1.

---

# 10. STATE GEOMETRY / DEVIATION CONCEPT

A central future idea is to represent state using more information than one arbitrary scalar.

Conceptually:

```text
G_t = [
    distance to state 1,
    distance to state 2,
    ...
]
```

If legitimate labelled states eventually exist, this might resemble:

```text
[d_W, d_N1, d_N2, d_N3, d_REM]
```

A scalar deviation/instability quantity currently discussed conceptually as something like:

```text
NSDI
```

may later be derived from the representation.

Potential temporal information includes:

```text
NSDI_t
ΔNSDI
slope
rolling change
trajectory
```

The exact mathematical definition is **NOT FINALIZED**.

Do not invent or assume a finalized NSDI equation.

State Geometry is a design direction, not current preprocessing implementation.

---

# 11. FUTURE TEMPORAL MODELLING CONCEPT

A future TCN could receive a temporal sequence:

```text
X[t-k], ..., X[t]
```

where each epoch-level representation might eventually contain some combination of:

```text
qEEG features
state geometry
deviation / instability
temporal derivatives
current-state probabilities
CNN / EEGNet embeddings
```

The model would ideally learn precursor trajectories rather than isolated abnormal epochs.

Examples of conceptual temporal patterns include:

```text
current-state similarity decreasing
candidate-next-state similarity increasing
spectral properties shifting
entropy changing
instability increasing
```

This architecture has not yet been established experimentally.

---

# 12. TRANSITION TARGET CONCEPT

The eventual objective is related to both:

```text
WHEN will a transition occur?
```

and:

```text
WHAT state is likely to come next?
```

The project does not want three independent classifiers such as:

```text
transition in 30 s?
transition in 60 s?
transition in 120 s?
```

because independent probabilities could violate cumulative consistency.

A future formulation may instead use mutually meaningful event-time/destination categories, conceptually such as:

```text
0–30 s      → destination state
30–60 s     → destination state
60–120 s    → destination state
no transition within 120 s
```

from which cumulative quantities could be derived:

```text
P(transition ≤ 30 s)
P(transition ≤ 60 s)
P(transition ≤ 120 s)
```

The exact target formulation is **NOT IMPLEMENTED AND NOT FINALIZED**.

Do not construct it during Preprocessing V1 unless explicitly instructed.

---

# 13. SCIENTIFIC CONSTRAINTS

The following are non-negotiable unless explicitly and scientifically reopened.

## Labels

* Never fabricate annotations.
* Never fabricate Sleep stages.
* Never create `y_sleep` without a legitimate annotation source.

## Temporal leakage

* Respect chronological structure.
* Do not introduce overlapping windows without analysing leakage.
* Do not allow train/test construction to leak future information.

## Boundaries

* Preserve recording boundaries.
* Preserve subject boundaries.
* Future temporal sequences must not cross boundaries artificially.

## Sampling frequency

* Use metadata-derived sampling frequencies.
* Account for sampling-frequency differences in filtering and spectral calculations.

## Channels

* Do not assume channel equivalence across datasets.
* Do not average channels without considering whether doing so is scientifically justified.
* Do not treat EOG/EMG/respiration/etc. as EEG merely because MNE assigned an incorrect initial type.

## Dataset/domain effects

* REST/SLEEP/CHB differences are not automatically brain-state differences.
* Cross-dataset comparisons require explicit control for domain effects.

## Signal processing

Code execution alone is insufficient evidence of methodological correctness.

Filtering, PSD, normalization, epoching, and feature extraction must be scientifically defensible.

---

# 14. OPEN QUESTIONS

These issues are intentionally unresolved.

Claude must not silently decide them without sufficient evidence or explicit discussion.

## Sleep supervision

* Is a legitimate Sleep hypnogram/annotation source available elsewhere?
* If not, what scientifically valid role should Sleep play before labelled data is obtained?

## State definition

* How should "state" ultimately be defined across the project?
* Can one unified state formalism legitimately span REST, SLEEP, and CHB?

## State Geometry

* What representation should define distance/similarity to a state?
* What mathematical distance or probabilistic formulation is defensible?
* Is a scalar NSDI-like measure genuinely useful?
* What should its mathematical definition be?

## Cross-channel representation

* When should EEG channels be kept separate?
* When, if ever, is averaging justified?

## Feature design

* Which qEEG features meaningfully help characterize state and transition dynamics?
* Which normalization strategy is appropriate?
* How should domain differences be handled?

## Temporal model

* Exact TCN input representation is unresolved.
* Exact receptive field is unresolved.
* Exact architecture/hyperparameters are unresolved.

## Transition targets

* Exact event/time target formulation is unresolved.
* Destination-state prediction formulation is unresolved.
* Supervised state-transition prediction depends on legitimate target labels.

---

# 15. COMPLETED / ESTABLISHED DISCOVERIES

The following discoveries have materially changed the project direction.

## Preprocessing must precede feature engineering

The earlier pipeline moved too quickly from raw EDF data into spectral feature extraction.

A trustworthy dedicated preprocessing layer is now required before relying on downstream qEEG representations.

## Sleep channel contamination problem identified

The Sleep PSG contains multiple physiological channel types, and initial MNE typing could cause non-EEG signals to enter EEG processing.

This is an established preprocessing defect that must be verified as corrected in the current notebook.

## Hypnogram assumption corrected

A previous agent inferred a Sleep hypnogram from a commented filename/path.

That inference was rejected.

No sleep-stage annotation source is considered available until actually verified.

## Zero-overlap epoch convention established

Current epoching uses:

```text
30-second windows
0 overlap
```

to maintain clean future horizon semantics.

---

# 16. DEPRECATED / REJECTED IDEAS

These ideas must NOT be revived silently.

## Fabricated Sleep hypnogram

Rejected.

A filename, commented path, or assumption does not establish that a hypnogram exists.

## Fabricated `y_sleep`

Rejected.

Without real stage annotations there is no legitimate supervised Sleep target.

## Treating dataset identity as physiological state

Rejected.

REST, SLEEP, and CHB are different datasets/domains and cannot simply become three brain-state labels.

## Premature downstream modelling

Rejected during the current milestone.

Do not move into:

* TCN training
* CNN / EEGNet modelling
* NSDI implementation
* transition prediction
* ARIMA
* Chronos
* final State Geometry

until Preprocessing V1 is explicitly considered sufficiently trustworthy.

## Arbitrary feature accumulation

Rejected as a design philosophy.

Do not add EEG features simply because they are commonly available.

Features should have a clear scientific or modelling purpose.

---

# 17. CURRENT HANDOFF INSTRUCTION

The immediate priority is to inspect the **actual current preprocessing notebook** and determine where Preprocessing V1 genuinely stands.

When beginning work:

1. establish the relevant notebook structure without repeatedly rereading the entire notebook
2. verify reported preprocessing corrections against actual code
3. inspect the target preprocessing issue and only necessary dependencies
4. classify findings as:

   * BUG
   * REQUIRED
   * OPTIONAL
   * LATER
5. correct only explicitly requested issues
6. preserve correct existing work
7. verify with runtime evidence
8. stop when the requested task is complete

The goal is not merely executable code.

The goal is a preprocessing foundation that is technically correct, scientifically defensible, temporally safe, and trustworthy enough to support later state/transition modelling.

---

# 18. FORECASTING TARGET EVOLUTION: 4-CLASS -> BINARY PREICTAL/INTERICTAL

Added 2026-09-08. This section distinguishes what is COMPLETE (and
preserved, not deleted) from what is COMPLETE-BUT-LABELING-ONLY from what
remains PLANNED. Do not treat anything in 18.4 as implemented.

## 18.1 Prior 4-class time-to-seizure forecasting -- COMPLETE, PRESERVED

Status: `COMPLETE (as a proof-of-concept), UNCHANGED, KEPT FOR PROJECT
HISTORY/COMPARISON`.

- `EEG_TCN_seizure_forecasting.ipynb`: CHB24 only (single patient, 12
  seizure-containing recordings). Target `forecast_class` in
  `{0-30s, 30-60s, 60-120s, >120s}`, cut from `time_to_next_seizure_sec`.
  Trained a TCN over 10-epoch (5-minute) qEEG feature sequences.
- `EEG_TCN_state_deviation_forecasting.ipynb`: CHB24 + CHB12 (17
  recordings, 2 patients). Same `forecast_class` target. Additionally
  introduces a **State Deviation Index** (`eeg_state_index`): a
  PCA-whitened Mahalanobis-equivalent distance of the 14 standardized qEEG
  features from a TRAIN-only "stable baseline" (non-seizure, `forecast_class
  == 3`/`>120s` epochs only, TRAIN recordings only -- scaler and PCA fit on
  this baseline exclusively, never on VAL/TEST). A TCN was trained on
  10-epoch sequences of this scalar index. Saved outputs (model weights,
  scaler, PCA, metrics, plots) live under
  `outputs/modeling/tcn_state_deviation_forecasting/`, untouched by the work
  in 18.3.
  - **Verified result (test set, n=318):** accuracy 78.9%, macro-F1 only
    0.22 -- the model predicts almost exclusively the majority class
    (`>120s`, F1=0.88); all three near-term classes (`0-30s`, `30-60s`,
    `60-120s`) have 0 precision/recall. This class-imbalance failure on the
    near-term/imminent classes is a large part of the supervisor's
    motivation for the binary reformulation in 18.3.

Neither notebook, nor any file under `outputs/modeling/`, was modified as
part of 18.3.

## 18.2 Postictal / previous-seizure metadata -- did not previously exist

Verified (2026-09-08) by direct inspection: prior to 18.3, neither
`features_chb24_forecasting.parquet` nor `features_chb12_forecasting.parquet`
contained any "time since previous seizure" or seizure end-time metadata.
`next_seizure_start_sec` / `time_to_next_seizure_sec` (computed in
`EEG_CHB24_preprocessing.ipynb` / `EEG_CHB12_preprocessing.ipynb`) only ever
looked forward. Both 4-class notebooks' definition of "far from a seizure"
(`forecast_class == 3`, i.e. `>120s` to the NEXT seizure) is therefore blind
to postictal state -- an epoch 10s after a seizure ended, if also `>120s`
before the next one, was previously treated identically to a genuinely quiet
epoch. This gap is exactly what 18.3 addresses.

## 18.3 Binary PREICTAL/INTERICTAL labeling -- LABELING COMPLETE AND VALIDATED; MODELING NOT STARTED

Status: `LABELS COMPLETE, VALIDATED, SAVED. NO MODEL HAS BEEN TRAINED ON
THEM YET.`

New notebook: `EEG_binary_preictal_labeling.ipynb` (labeling only -- no
model, no scaling/normalization, no train/val/test split). Reads
`features_chb24_forecasting.parquet` / `features_chb12_forecasting.parquet`
read-only; neither file, nor either 4-class notebook, was modified.

New metadata (derived from the CHB-MIT `chbXX-summary.txt` annotation files
via `parse_chb_summary`, the same parser already used in
`EEG_CHB24_preprocessing.ipynb` / `EEG_CHB12_preprocessing.ipynb` -- not
approximated from epoch-level flags; cross-checked to exactly reproduce the
existing `next_seizure_start_sec` column before being trusted):
`time_since_previous_seizure_sec`, `seizure_id`, `next_seizure_id`,
`previous_seizure_id`, `previous_seizure_end_sec`.

Reusable labeling function: `make_binary_labels(df, preictal_minutes,
exclusion_minutes=30)`. PREICTAL = `y_seizure==0` and `0 <
time_to_next_seizure_sec <= preictal_minutes*60` and not postictal-
contaminated. INTERICTAL = `y_seizure==0` and `>= exclusion_minutes` (>=30,
enforced) from both the next seizure and the end of the previous seizure.
Everything else is excluded with an explicit `exclusion_reason`
(`seizure_overlap`, `postictal_exclusion`, `ambiguous_preictal_gap`,
`seizure_onset_boundary`) rather than forced into a class.

Output: `outputs/labels_binary_preictal.parquet` / `.csv` -- ONE combined
CHB24+CHB12 table (2040 rows), with `binary_label_h{5,15,30}` /
`exclusion_reason_h{5,15,30}` column pairs (not three duplicated tables),
plus every metadata column (`patient_id`, `subject_id`, `recording_id`,
`seizure_id`/`next_seizure_id`/`previous_seizure_id`, `epoch_idx`,
`t_start_sec`/`t_end_sec`) needed for a future leave-one-seizure-out split.

**Verified label counts** (exclusion_minutes=30, both patients combined,
2040 total epochs):

```text
H=5 min : PREICTAL=170, INTERICTAL=372, EXCLUDED=1498
H=15 min: PREICTAL=445, INTERICTAL=372, EXCLUDED=1223
H=30 min: PREICTAL=732, INTERICTAL=372, EXCLUDED= 936
```

INTERICTAL count is constant across horizons (the exclusion window is fixed
at 30 min); PREICTAL grows with the horizon as expected.

All 5 validation checks (no seizure-overlap in either class; every
PREICTAL epoch inside `(0, H]`; every INTERICTAL epoch `>` exclusion
distance from both neighbors; no PREICTAL epoch postictal-contaminated;
no nulls in chronological/identity metadata) pass for all three horizons.

**Key finding surfaced by validation:** only 19 of the 35 total annotated
seizures (16 CHB24 + 19 CHB12) contribute at least one PREICTAL epoch at
ANY horizon. The rest are seizures in a cluster (mostly CHB12, whose
recordings often contain 2-5 seizures within minutes of each other) whose
entire nominal preictal window falls inside the 30-minute postictal
exclusion of the immediately preceding seizure, so `make_binary_labels`
correctly excludes them rather than fabricating a contaminated PREICTAL
label. This is a real property of the data, not a bug, and should be
considered when scoping any future leave-one-seizure-out design (many
"seizures" have no usable PREICTAL support at all).

## 18.4 Explicitly NOT implemented yet (planned, future tasks only)

Per the supervisor's task scope, none of the following exist yet and must
not be treated as implemented:

- Patient-specific normalization/scaling for the binary task.
- Any classifier/model (TCN or otherwise) trained on `binary_label_h*`.
- Any new evaluation metrics for the binary task.
- Any channel-level changes.
- Expansion beyond the existing CHB24 + CHB12 patients.
- Any train/val/test split or leave-one-seizure-out split for the binary
  labels (the metadata to support LOSO is preserved, but the split itself
  is not chosen).

---

# 19. PATIENT-SPECIFIC NORMALIZATION (NO LEAKAGE)

Added 2026-09-08, after implementation and validation.

Status: `NORMALIZATION FUNCTION IMPLEMENTED, LEAKAGE-CHECKED, DEMONSTRATED
ON BOTH CURRENTLY AVAILABLE PATIENTS. NO MODEL HAS BEEN TRAINED ON THE
SCALED FEATURES YET.`

## 19.1 Prior normalization state (verified by inspection)

- `EEG_modeling.ipynb` (CHB01 only) and `EEG_TCN_seizure_forecasting.ipynb`
  (CHB24 only): `StandardScaler` fit on TRAIN rows only, per split --
  correctly leakage-free, and trivially per-patient since each involves a
  single patient.
- `EEG_TCN_state_deviation_forecasting.ipynb` (CHB24 + CHB12): a single
  `StandardScaler` (and downstream PCA) fit on TRAIN "stable baseline"
  rows **pooled across both patients**. Fit-on-TRAIN-only (no train/test
  leakage), but this DOES mix two patients' EEG statistics into one
  scaler -- a cross-patient leakage/contamination gap, not a temporal one.
  A non-destructive markdown deprecation note was added immediately before
  that notebook's scaler cell explaining this; no code in that notebook
  was changed, and its saved outputs under
  `outputs/modeling/tcn_state_deviation_forecasting/` remain valid for
  project-history comparison.
- `outputs/labels_binary_preictal.parquet` (from Section 18) had no
  scaler applied at all prior to this task.

## 19.2 New implementation

New notebook: `EEG_patient_normalization.ipynb`. Reads
`outputs/labels_binary_preictal.parquet` read-only; no existing file was
modified except the deprecation-note insertion described above.

Reusable functions (designed to plug into a future leave-one-seizure-out
loop unchanged -- they take an explicit `train_mask` rather than deciding
the split themselves):

- `fit_patient_scalers(df, patient_col, feature_cols, train_mask)` -- one
  `StandardScaler` per unique patient, fit only on that patient's TRAIN
  rows.
- `transform_with_patient_scalers(df, patient_col, feature_cols, scalers)`
  -- transforms every row using its own patient's fitted scaler; raises if
  any row's patient has no fitted scaler.
- `patient_specific_train_test_scale(...)` -- convenience wrapper
  composing the two above.

Only the 14 qEEG feature columns are scaled (written to new `*_scaled`
columns, raw features preserved alongside them); every identifier, label,
timestamp, and exclusion-flag column is left untouched.

For this demonstration, TRAIN/TEST folds are recording-level, reusing the
exact recording assignments already established in
`EEG_TCN_state_deviation_forecasting.ipynb` (its TRAIN+VAL recordings ->
this task's TRAIN; its TEST recordings -> this task's TEST). This is a
convenience fold for demonstrating the scaler, not a new split decision --
leave-one-seizure-out itself remains a separate future task.

## 19.3 Verified results

Patients processed: `chb12`, `chb24` (the only two currently available).

```text
chb12: TRAIN=480 epochs, TEST=120 epochs
chb24: TRAIN=1200 epochs, TEST=240 epochs
```

14 scaled feature columns produced per patient. All 4 leakage checks
passed for both patients:
1/2. Each scaler's `n_samples_seen_` exactly equals that patient's TRAIN
row count (never the total including TEST); means independently
recomputed from TRAIN-only rows match `scaler.mean_` exactly.
3. Each patient's fitted mean is NOT reproducible from any other patient's
TRAIN rows (no cross-patient pooling).
4. Fitted feature column order is identical to `FEATURE_COLS` for every
patient.

Before/after check (CHB24, one fold): TRAIN-scaled features have mean~0,
std~1 (exact, since the scaler was fit on exactly those rows); TEST-scaled
features do NOT (mean ~2.0-4.4, std ~2.4-6.3) -- the correct, expected
signature of a leakage-free transform, and also evidence that CHB24's
TEST recordings (`r01`, `r21`) have genuinely different raw qEEG
statistics than its TRAIN recordings.

Output: `outputs/features_patient_scaled.parquet` / `.csv` (2040 rows x 51
columns) -- new file, nothing existing overwritten.

## 19.4 Explicitly NOT implemented yet

- Any classifier trained on the scaled features.
- ~~Leave-one-seizure-out fold definition~~ -- see Section 20 (implemented
  2026-09-08, after this section was originally written).
- New evaluation metrics, channel-level changes, or expansion beyond
  CHB24/CHB12.

---

# 20. LEAVE-ONE-SEIZURE-OUT (LOSO) EVALUATION SPLITTING

Added 2026-09-08, after implementation and validation.

Status: `LOSO FOLD CONSTRUCTION IMPLEMENTED, LEAKAGE-CHECKED (57/57 folds,
9 checks each), VALIDATED FOR BOTH CURRENT PATIENTS AND ALL 3 HORIZONS. NO
CLASSIFIER HAS BEEN TRAINED ON THESE FOLDS YET.`

## 20.1 Overview

New notebook: `EEG_loso_evaluation_splitting.ipynb`. Reads
`outputs/labels_binary_preictal.parquet` (RAW/unscaled features) read-only
-- deliberately NOT `outputs/features_patient_scaled.parquet`, since that
file's `*_scaled` columns were produced by a single fixed recording-level
split and would leak LOSO-fold TEST information into scaler statistics if
reused. No existing file was modified.

## 20.2 Seizure inventory and eligibility (re-verified, not assumed)

`chb12`: 19 annotated seizures across 5 recordings. `chb24`: 16 annotated
seizures across 12 recordings. Total 35, matching Section 18's prior
count. Eligibility (>=1 PREICTAL epoch at a given horizon) was
independently re-verified per horizon rather than assumed constant:

```text
H= 5min: chb12 5/19 eligible, chb24 14/16 eligible (19 total, matches Section 18)
H=15min: chb12 5/19 eligible, chb24 14/16 eligible (19 total)
H=30min: chb12 5/19 eligible, chb24 14/16 eligible (19 total)
```

The eligible set is IDENTICAL across all three horizons for this dataset
(a seizure with zero clean preictal epochs at 5 min also has zero at 15/30
min -- the epochs consumed are the same `postictal_exclusion` /
`seizure_overlap` epochs regardless of horizon width). Every ineligible
seizure's exclusion reason was computed from real data and saved to
`outputs/loso_ineligible_seizures.csv` (48 rows = 16 ineligible seizures x
3 horizons) -- dominant reasons are `postictal_exclusion` (clustered
seizures) and, for a few CHB12 seizures whose neighbors are extremely
close together, `seizure_overlap` (the would-be preictal window of one
seizure is itself occupied by a DIFFERENT seizure's overlap).

## 20.3 Fold definition

One fold per eligible seizure (57 total = 19 eligible seizures x 3
horizons). PREICTAL epochs belong to the fold of their own
`next_seizure_id`. INTERICTAL epochs belong to `next_seizure_id` if
defined, else `previous_seizure_id` (every epoch in every currently-loaded
recording has at least one of these defined, verified programmatically).
Recording-level fold assignment was considered and REJECTED: CHB24's `r01`
and `r03` each contain two eligible seizures, so holding out a whole
recording would incorrectly also remove the OTHER eligible seizure's
PREICTAL epochs from TRAIN.

Normalization is fit fresh inside every fold via
`fit_patient_scalers`/`transform_with_patient_scalers` (reused verbatim
from `EEG_patient_normalization.ipynb`), on that fold's TRAIN rows only.

## 20.4 Leakage checks

9 checks run for EVERY fold (not a sample): TRAIN/TEST disjoint; held-out
seizure's PREICTAL epochs never in TRAIN; `scaler.n_samples_seen_` exactly
equals TRAIN row count; independently-recomputed TRAIN-only mean matches
`scaler.mean_`; exactly one patient per fold; fitted feature-column order
matches `FEATURE_COLS`; only `PREICTAL`/`INTERICTAL` rows used (excluded
epochs never enter a fold); no seizure-overlapping (`y_seizure==1`) row
used; chronological metadata (`recording_id`/`epoch_idx`/`t_start_sec`/
`t_end_sec`) non-null. **57/57 folds passed all 9 checks.**

## 20.5 Important structural findings surfaced by validation

- `chb_s24_r07_sz0` has only 1 TEST PREICTAL epoch at every horizon (its
  seizure begins only 38s into the recording, leaving almost no
  pre-seizure history) -- any future evaluation on this fold will be
  extremely noisy.
- 10 of the 19 folds (all 5 CHB12 folds, plus CHB24's `r01_sz0`, `r01_sz1`,
  `r03_sz0`, `r03_sz1`, `r04_sz0`) have **0 TEST INTERICTAL epochs** at
  every horizon: either the recording is so seizure-dense that no epoch in
  it is ever >=30min from every seizure (CHB24 r01/r03/r04), or (CHB12)
  the eligible seizure is always the recording's FIRST, and that
  recording's few INTERICTAL epochs are contextually tied to a LATER,
  ineligible seizure instead. Any future evaluation on these folds cannot
  measure specificity/false-positive rate in isolation -- a future
  modeling task will need to decide how to handle this (e.g. aggregate
  metrics across folds rather than trusting any single fold's specificity).

## 20.6 Outputs

- `outputs/loso_fold_manifest.parquet` / `.csv` (57 rows): patient_id,
  horizon_minutes, fold_id, held_out_seizure_id, train/test preictal and
  interictal counts, train_total, test_total.
- `outputs/loso_ineligible_seizures.csv` (48 rows): seizure_id + diagnosed
  exclusion reason per patient/horizon.
- `outputs/loso_epoch_fold_context.parquet` (2463 rows, long format across
  horizons): per-epoch fold-context assignment, so a future modeling
  notebook can reconstruct any fold's TRAIN/TEST row set without
  recomputing `assign_fold_context()`.

## 20.7 Preserved existing work

`EEG_TCN_state_deviation_forecasting.ipynb`'s recording-level TRAIN/VAL/TEST
split and `EEG_patient_normalization.ipynb`'s recording-level demonstration
fold are both untouched -- kept for historical comparison. LOSO is an
additional, separate evaluation path.

## 20.8 Explicitly NOT implemented yet

- Any Logistic Regression / Random Forest / TCN training or evaluation on
  these folds.
- New evaluation metrics.
- Channel representation changes.
- Expansion beyond CHB24/CHB12.

---

# 21. STATUS SUMMARY (binary labeling -> normalization -> LOSO -> LR baseline)

- Binary PREICTAL/INTERICTAL labeling (5/15/30 min horizons): **COMPLETED**
  (Section 18).
- Patient-specific, TRAIN-only normalization: **COMPLETED** (Section 19).
- LOSO evaluation splitting: **COMPLETED** (Section 20).
- Seizure-prediction metric framework (seizure sensitivity, false
  alarms/hour, time in warning, AUC-PR, pooled event/epoch aggregation):
  **COMPLETED** (Section 22).
- Logistic Regression LOSO baseline (both patients, all 3 horizons):
  **COMPLETED** (Section 22).
- **STILL PENDING** -- not started:
  - Random Forest on these LOSO folds.
  - TCN on these LOSO folds.
  - Channel-wise representation changes.
  - Expansion beyond the current 2 patients (chb12, chb24) / 10+ patients.
  - Final comparative experiments (LR vs RF vs TCN).
  - Final preprocessing re-audit before paper methodology is frozen
    (Preprocessing V1's "IN PROGRESS" status, Section 6, has not been
    revisited as part of this update).

---

# 22. SEIZURE-PREDICTION METRICS + LOGISTIC REGRESSION LOSO BASELINE

Added 2026-09-09, after implementation, self-testing, execution, and
cross-check validation.

Status: `METRIC FRAMEWORK SELF-TESTED. LOGISTIC REGRESSION FIT AND
EVALUATED ON ALL 57 LOSO FOLDS (2 PATIENTS x 3 HORIZONS x 19 ELIGIBLE
SEIZURES). RANDOM FOREST AND TCN NOT STARTED.`

## 22.1 Metric framework (prerequisite, built this task)

New notebook: `EEG_seizure_prediction_metrics.ipynb`. No model-specific
code; defines and self-tests (synthetic examples, not real data) reusable
metric functions later copied verbatim into the modeling notebook, the
same reuse convention already established between
`EEG_patient_normalization.ipynb` and `EEG_loso_evaluation_splitting.ipynb`.

Primary (event-level) metrics, `fold_seizure_event_metrics()`:
- **Seizure sensitivity**: per fold, whether >=1 TEST PREICTAL epoch was
  predicted PREICTAL (event-based; a LOSO fold IS one held-out seizure).
- **Time in warning**: `time_to_next_seizure_sec` of the *earliest*
  correctly-alarmed PREICTAL epoch. Does NOT require the alarm to persist
  continuously afterward (documented simplifying choice for this first
  baseline). `NaN` (never 0) when the seizure was not detected.
- **False alarms/hour**: TEST INTERICTAL epochs predicted PREICTAL are
  merged into "alarm events" (maximal runs of `epoch_idx`-consecutive
  positive predictions) before counting, so one sustained alarm is not
  inflated into many; divided by TEST-interictal hours. `NaN` (never 0)
  when a fold has 0 TEST interictal epochs (30 of 57 fold-rows here --
  matches the "10 of 19 folds have 0 TEST interictal at every horizon"
  finding already established in Section 20.5: 10 folds x 3 horizons = 30).

Secondary (epoch-level) metrics, `fold_epoch_metrics()`: accuracy,
precision/recall/F1 (positive=PREICTAL, `zero_division=np.nan` so an
undefined value is never silently 0), AUC-PR (explicitly `NaN`, not
sklearn's degenerate 1.0, when TEST has only one class).

Pooled aggregation, `pool_event_metrics()` / `pool_epoch_metrics()`: event
counts and interictal-hours are **summed** across folds before dividing
once (never a naive mean of per-fold rates); epoch-level metrics are
computed on the **concatenation** of TEST epochs across folds. Both
documented as revisable methodological choices, not literature-standard
reproductions.

## 22.2 Logistic Regression LOSO baseline

New notebook: `EEG_logistic_loso_binary.ipynb`. Reads
`outputs/labels_binary_preictal.parquet` (RAW/unscaled features) read-only.
Fold-construction functions (`compute_seizure_eligibility`,
`assign_fold_context`, `fit_patient_scalers`, `transform_with_patient_scalers`,
`build_loso_fold`, `validate_loso_fold`) copied verbatim from
`EEG_loso_evaluation_splitting.ipynb` and re-run fresh (not read from its
saved manifest, which only stores counts) -- then **cross-checked against
that saved manifest and found to match exactly on all 57 folds**
(train/test totals, preictal/interictal counts), confirming no divergence
from the already-validated fold construction.

**Model**: `LogisticRegression(class_weight="balanced", random_state=42,
solver="lbfgs", max_iter=1000)`, `C` left at sklearn's default (not tuned).
`class_weight="balanced"` chosen after inspecting per-fold TRAIN prevalence
from the existing manifest (median PREICTAL prevalence 0.514 at H=5,
ranging 0.251-0.826 across folds/horizons; 36/57 folds outside [0.4, 0.6])
-- computed by sklearn from each fold's own TRAIN `y` at `.fit()` time, so
inherently TRAIN-only, never tuned via TEST. Decision threshold fixed at
0.5, not optimized on TEST. Compared against
`DummyClassifier(strategy="most_frequent")` fit identically per-fold, as
the naive/majority-class sanity baseline.

**Patient-specific invariant**: verified structurally (folds are built from
a single-patient `patient_df` before any split) and re-asserted explicitly
in the main loop, for every fold -- CHB12 and CHB24 are never pooled into
one model.

**Verified pooled overall results (both patients, LR)**:

```text
H= 5min: sensitivity=0.947 (18/19 seizures), FA/hour=13.65, AUC-PR=0.536
H=15min: sensitivity=0.947 (18/19 seizures), FA/hour=13.29, AUC-PR=0.650
H=30min: sensitivity=0.947 (18/19 seizures), FA/hour=12.57, AUC-PR=0.736
```

**Per-patient split matters and must not be hidden behind the pooled
number**: CHB12 (5/5 eligible seizures, all with 0 TEST interictal epochs
at every horizon) shows sensitivity=1.0 with FA/hour and AUC-PR **both
undefined (NaN)** -- there is no interictal TEST data to measure a false
alarm rate or a meaningful AUC-PR against for this patient with the
current data. CHB24 (13/14 of its 14 eligible seizures detected) has real,
non-degenerate FA/hour (~12-14/hour) and AUC-PR (0.30-0.59, improving with
horizon). The pooled "overall" numbers above are therefore driven almost
entirely by CHB24 for FA/hour and AUC-PR.

**Sanity checks passed**: Logistic Regression's predicted-positive rate on
TEST (66-79% across horizons) is not degenerate (not <2% or >98%), unlike
the earlier 4-class TCN's near-total majority-class collapse
(Section 18.1). At H=30min specifically, the naive dummy baseline also
reaches sensitivity=1.0 and a *low* FA/hour (3.23) -- because at that
horizon TRAIN PREICTAL prevalence exceeds 50% in most folds, so
"most-frequent" already means "always predict PREICTAL", and because
constant positive predictions over a contiguous interictal segment merge
into very few alarm *events* under this notebook's event-counting
definition (a known, documented consequence of merging consecutive alarms,
not a flaw specific to the dummy). This means FA/hour and sensitivity
*alone* do not fully distinguish "genuinely time-varying detector" from
"a classifier that outputs mostly-constant positive predictions" -- AUC-PR
and the probability-distribution overlap (LR's TEST P(PREICTAL) for true
PREICTAL vs INTERICTAL, Section 22 notebook Section 10) are the more
informative secondary signals for that at H=30.

**Coefficients** (standardized features, pooled across all 57 folds):
`alpha` (mean coef +1.23, positive in 89% of folds) and `rel_delta` (+0.30,
positive in 96% of folds) are the most consistently PREICTAL-associated
features; `delta_beta_ratio` (-1.12) is the most negative on average but
has the least consistent sign (positive in only 30% of folds) -- flagged
explicitly as unstable, not reported as a stable finding. **Not
interpreted as causal biomarkers** -- descriptive of this baseline on this
2-patient sample only.

**Outputs**: `outputs/modeling/logistic_loso_binary/` -- `predictions.parquet`
/ `.csv` (per-epoch, both LR and dummy), `fold_metrics.csv`,
`patient_horizon_summary.csv`, `overall_horizon_summary.csv`,
`coefficients_long.csv` + 2 summary tables, `experiment_config.json`, and
`plots/` (PR curves, confusion matrices, probability distributions,
cross-horizon metric comparison). All previously existing outputs
(`EEG_modeling.ipynb`'s baseline, both 4-class TCN notebooks and their
saved artifacts, `features_patient_scaled.parquet`,
`loso_fold_manifest.parquet`) are untouched.

## 22.3 Explicitly NOT implemented yet

- Random Forest or TCN on these LOSO folds.
- Any threshold optimization (fixed at 0.5) or hyperparameter search (`C`
  left at sklearn's default).
- Channel-wise representation changes.
- Expansion beyond CHB12/CHB24.
- Statistical significance testing on any pooled metric.
- A resolution to the CHB12 zero-TEST-interictal structural gap (Section
  20.5) -- it is surfaced and quantified here (NaN, not papered over), not
  solved.

---

# 23. RANDOM FOREST LOSO BASELINE (BINARY, SAME METHODOLOGY AS LOGISTIC REGRESSION)

Added 2026-09-14, after implementation, execution (`jupyter nbconvert
--execute`, clean run, no errors), and inspection of the actual saved
outputs.

Status: `RANDOM FOREST FIT AND EVALUATED ON ALL 57 LOSO FOLDS (2 PATIENTS x
3 HORIZONS x 19 ELIGIBLE SEIZURES), SAME FOLDS AS LOGISTIC REGRESSION.
OUTPUTS SAVED AND INSPECTED. TCN NOT STARTED.`

## 23.1 Scope and reuse

New notebook: `EEG_random_forest_loso_binary.ipynb`. Reads
`outputs/labels_binary_preictal.parquet` (RAW/unscaled features) read-only,
same as `EEG_logistic_loso_binary.ipynb`. Fold-construction functions
(`compute_seizure_eligibility`, `assign_fold_context`,
`fit_patient_scalers`, `transform_with_patient_scalers`, `build_loso_fold`,
`validate_loso_fold`) and metric functions (`fold_seizure_event_metrics`,
`fold_epoch_metrics`, `pool_epoch_metrics`, `pool_event_metrics`) copied
verbatim from `EEG_logistic_loso_binary.ipynb`. **Only the estimator
changes** -- `RandomForestClassifier` in place of `LogisticRegression`;
patients, features, labels, horizons, postictal exclusion, eligible
seizures, LOSO folds, TRAIN/TEST definition, patient-specific
normalization, leakage rules, and metric definitions are all identical and
unchanged.

**Fold-for-fold cross-check (new, beyond what the LR notebook did):** this
notebook additionally merges its own `fold_summary_df` against the LR run's
saved `fold_metrics.csv` and asserts `n_train`, `n_test`,
`train_preictal_count`, `train_interictal_count` match exactly for all 57
folds -- confirmed a genuinely fair, apples-to-apples comparison (only the
estimator differs), not just a repeat of the earlier fold-construction
validation.

## 23.2 Model configuration

```text
RandomForestClassifier(
    n_estimators=100,       # sklearn default, not enlarged/tuned
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,               # parallelism only, does not affect results
)
```

Every other hyperparameter (`max_depth`, `min_samples_split`,
`min_samples_leaf`, `max_features`, ...) left at sklearn's default -- no
hyperparameter search was performed, consistent with the task scope.

**Class imbalance choice, documented explicitly:** LR used
`class_weight="balanced"`. RF's closest analogue is also
`class_weight="balanced"` (weights computed once from the fold's whole
TRAIN `y`, mirroring what LR does) rather than `"balanced_subsample"`
(recomputed per bootstrap resample) -- chosen as the more directly
comparable mechanism. Computed by sklearn strictly from each fold's own
TRAIN labels at `.fit()` time, never TEST.

Naive baseline: `DummyClassifier(strategy="most_frequent")`, refit
independently in this notebook (same construction as the LR notebook's).

## 23.3 Verified pooled overall results (both patients, Random Forest)

From `outputs/modeling/random_forest_loso_binary/overall_horizon_summary.csv`:

```text
H= 5min: sensitivity=0.842 (16/19), FA/hour=16.89, AUC-PR=0.529
H=15min: sensitivity=0.947 (18/19), FA/hour=18.32, AUC-PR=0.731
H=30min: sensitivity=0.947 (18/19), FA/hour=15.81, AUC-PR=0.768
```

Per-patient split (`patient_horizon_summary.csv`): CHB12 (all 5 eligible
seizures, 0 TEST interictal epochs at every horizon, same structural gap as
LR) -- sensitivity=1.0, FA/hour and AUC-PR undefined (NaN) for the same
reason as LR. CHB24 -- sensitivity 0.786 (11/14) at H=5, 0.929 (13/14) at
H=15/30; FA/hour 16.9-18.3/hour; AUC-PR 0.274-0.574.

## 23.4 Logistic Regression vs Random Forest comparison

Read directly from the two runs' saved `overall_horizon_summary.csv` files
(`outputs/modeling/random_forest_loso_binary/lr_vs_rf_comparison_overall.csv`
holds this exact table):

```text
Horizon | Model                | Sensitivity | Detected/Elig | FA/hour | AUC-PR
5 min   | Logistic Regression  | 0.947       | 18/19         | 13.65   | 0.536
5 min   | Random Forest        | 0.842       | 16/19         | 16.89   | 0.529
15 min  | Logistic Regression  | 0.947       | 18/19         | 13.29   | 0.650
15 min  | Random Forest        | 0.947       | 18/19         | 18.32   | 0.731
30 min  | Logistic Regression  | 0.947       | 18/19         | 12.57   | 0.736
30 min  | Random Forest        | 0.947       | 18/19         | 15.81   | 0.768
```

**Interpretation (from the notebook's own Section 16, not hardcoded here):**

1. **AUC-PR:** RF is slightly worse at H=5 (-0.007), better at H=15 (+0.081)
   and H=30 (+0.032). Improvement is modest and horizon-dependent, not
   uniform.
2. **FA/hour:** RF is *worse* (higher) than LR at every horizon it is
   measurable (+3.2 to +5.0/hour) -- RF does **not** reduce false alarms
   here.
3. **Sensitivity:** RF is lower at H=5 (0.842 vs 0.947, missing 2 more
   seizures) and equal at H=15/H=30.
4. **Driven by CHB24:** CHB12 contributes 0 TEST interictal epochs at every
   horizon for both models (FA/hour, AUC-PR = NaN there) -- every pooled
   FA/hour and AUC-PR number above is mechanically CHB24-only.
5. **Bottleneck:** the largest |AUC-PR delta| across horizons is 0.081 (at
   H=15). Given identical features and folds, this modest, inconsistently-
   signed delta is more consistent with "the qEEG feature representation is
   the binding constraint" than with "Random Forest is a materially better
   classifier for this problem" -- it does not clearly beat the simpler LR
   baseline.
6. **Overfitting -- confirmed and material:** mean TRAIN accuracy vs pooled
   TEST accuracy (`outputs/modeling/random_forest_loso_binary/`, notebook
   Section 10): CHB24 TRAIN accuracy is 0.996-1.000 at every horizon while
   pooled TEST accuracy is only 0.465-0.565 (gap 0.44-0.54). CHB12's gap is
   much smaller (0.000-0.035) because those folds have no TEST interictal
   epochs, making TEST accuracy trivially high regardless of overfitting.
   Default `max_depth=None` grows fully unpruned trees; this is the
   textbook overfitting signature for tree ensembles and is the most
   important caveat on the H=15/H=30 AUC-PR gains above.
7. **H=30 majority-baseline caveat still applies:** all 19/19 folds have
   TRAIN PREICTAL prevalence > 0.5 at H=30 (same structural finding as LR,
   Section 22.2) -- `dummy_most_frequent` at H=30 again reaches
   sensitivity=1.0 with low FA/hour (3.23/hour) purely from prevalence, for
   the same reason documented for LR. High sensitivity/low FA/hour at H=30
   is not on its own evidence of a genuinely time-varying detector, for RF
   any more than for LR.

**Feature importance** (`feature_importances_summary_overall.csv`, pooled
across all 57 folds): `entropy` (0.114), `rel_beta` (0.113), `beta`
(0.108), and `delta_beta_ratio` (0.097, most rank-stable at 94.7% of folds
in that fold's own top-5) are the most important features on average.
`std`/`var`/`rms` are consistently least important (never in any fold's
top-5). Not interpreted as causal biomarkers, same caveat as LR's
coefficients (Section 22.2) -- descriptive of this baseline on this
2-patient sample only.

## 23.5 Leakage / validation results

All checks from the LR notebook reused and re-passed here, plus the new
fold-for-fold cross-check (23.1): TRAIN/TEST disjoint; held-out seizure's
PREICTAL epochs never in TRAIN; scaler fit/transform TRAIN-only per patient
per fold; exactly one patient per fold; feature order matches
`FEATURE_COLS`; only PREICTAL/INTERICTAL rows used; no seizure-overlapping
rows; chronological metadata non-null; **57/57 folds** match
`loso_fold_manifest.parquet` exactly; **57/57 folds** match the LR run's
own `fold_metrics.csv` train/test composition exactly. Notebook executed
end-to-end via `jupyter nbconvert --execute` with no errors; `n_folds_total
== 57` asserted in-notebook and confirmed in the saved
`experiment_config.json`.

## 23.6 Outputs

`outputs/modeling/random_forest_loso_binary/` -- `predictions.parquet` /
`.csv` (per-epoch, both RF and dummy), `fold_metrics.csv`,
`patient_horizon_summary.csv`, `overall_horizon_summary.csv`,
`feature_importances_long.csv` + 3 summary tables,
`lr_vs_rf_comparison_overall.csv`, `lr_vs_rf_comparison_by_patient.csv`,
`experiment_config.json`, and `plots/` (PR curves, confusion matrices,
probability distributions, cross-horizon metric comparison, feature
importance bar chart). `outputs/modeling/logistic_loso_binary/` and all
other previously existing outputs were asserted untouched at both the start
and end of the notebook run, and confirmed untouched by inspection.

## 23.7 Explicitly NOT implemented yet

- TCN on these LOSO folds.
- Any hyperparameter search (`n_estimators`, tree depth, etc. left at
  sklearn defaults) or threshold optimization (fixed at 0.5).
- Any fix for the RF overfitting signature identified in 23.4.6 (e.g. depth
  limiting, `min_samples_leaf` tuning) -- surfaced and quantified, not
  solved, per task scope.
- Channel-wise representation changes.
- Expansion beyond CHB12/CHB24.
- Statistical significance testing on any pooled metric or on the LR-vs-RF
  deltas.
- A resolution to the CHB12 zero-TEST-interictal structural gap (Section
  20.5) -- still present, identically for both models.

---

# 24. STATUS SUMMARY UPDATE (post Random Forest)

- Binary PREICTAL/INTERICTAL labeling, patient-specific normalization, LOSO
  evaluation splitting, seizure-prediction metrics, Logistic Regression
  baseline: **COMPLETED** (Sections 18-22, unchanged by this update).
- Random Forest LOSO baseline (both patients, all 3 horizons, same 57
  folds): **COMPLETED** (Section 23).
- **STILL PENDING** -- not started:
  - TCN on these LOSO folds.
  - Any hyperparameter tuning for either LR or RF (both deliberately
    un-tuned first baselines).
  - A fix for RF's identified overfitting (Section 23.4.6).
  - Channel-wise representation changes.
  - Expansion beyond the current 2 patients (chb12, chb24) / 10+ patients.
  - Final comparative experiments (LR vs RF vs TCN) -- LR vs RF is done
    (Section 23.4); TCN is not yet in this comparison.
  - Final preprocessing re-audit before paper methodology is frozen
    (Preprocessing V1's "IN PROGRESS" status, Section 6, still not
    revisited).

---

# 25. TASK RECORD -- RANDOM FOREST LOSO BASELINE (2026-09-14)

This section is the mandatory structured record of exactly this task, per
the supervisor's explicit reporting requirement. Section 23 above holds the
full narrative detail; this section is the checklist-format summary. Both
describe the same, single, already-executed task -- neither supersedes the
other.

## 25.1 Task completed

Task: implement a Random Forest baseline under the exact same binary LOSO
methodology already validated for Logistic Regression (Section 22), so that
Logistic Regression vs Random Forest differ ONLY in the estimator.

Status: **COMPLETE.** Notebook implemented, executed end-to-end with no
errors, outputs saved, outputs inspected (by reading the actual saved
CSV/JSON files, not by trusting notebook print statements alone), fold and
leakage checks passed, results reported (Section 23.3-23.4 and 25.7 below).

## 25.2 Files created

- `EEG_random_forest_loso_binary.ipynb` (repo root) -- new notebook, 33
  cells, mirrors `EEG_logistic_loso_binary.ipynb`'s section structure.
- `outputs/modeling/random_forest_loso_binary/` (new directory) containing:
  `predictions.parquet`, `predictions.csv`, `fold_metrics.csv`,
  `patient_horizon_summary.csv`, `overall_horizon_summary.csv`,
  `feature_importances_long.csv`,
  `feature_importances_summary_overall.csv`,
  `feature_importances_summary_by_horizon.csv`,
  `feature_importances_summary_by_patient_horizon.csv`,
  `lr_vs_rf_comparison_overall.csv`, `lr_vs_rf_comparison_by_patient.csv`,
  `experiment_config.json`, and `plots/` (`pr_curves_overall_by_horizon.png`,
  `confusion_matrices_rf.png`, `probability_distributions.png`,
  `primary_metrics_by_horizon.png`, `feature_importance_overall.png`).

## 25.3 Files modified

- `.claude/skills/eeg-context/project_state.md` -- appended Sections
  23-25 (this record) and updated the "Last intentionally updated" date
  (top of file) from 2026-09-08 to 2026-09-14. No prior section's text was
  rewritten or deleted.

No other existing file was modified. In particular, verified by direct
inspection (file listing + timestamps) that every file under
`outputs/modeling/logistic_loso_binary/` still carries its original
2026-09-09 16:12 timestamp -- untouched by this task.

## 25.4 Implementation

Reused verbatim (copied, not reimplemented) from
`EEG_logistic_loso_binary.ipynb`:
- Fold-construction: `compute_seizure_eligibility`, `assign_fold_context`,
  `fit_patient_scalers`, `transform_with_patient_scalers`,
  `build_loso_fold`, `validate_loso_fold` (9 leakage checks per fold).
- Metrics: `fold_seizure_event_metrics`, `fold_epoch_metrics`,
  `pool_epoch_metrics`, `pool_event_metrics`, `_count_alarm_events`,
  `validate_predictions_df`.
- 14 `FEATURE_COLS` (std, var, rms, delta, theta, alpha, beta, rel_delta,
  rel_theta, rel_alpha, rel_beta, theta_alpha_ratio, delta_beta_ratio,
  entropy), `HORIZONS=[5,15,30]`, `PATIENTS=[chb12, chb24]`,
  `RANDOM_STATE=42`, `THRESHOLD=0.5` -- asserted byte-for-byte identical to
  the LR run's saved `experiment_config.json` at notebook runtime (not just
  visually compared).

New for this task:
- Estimator: `RandomForestClassifier(n_estimators=100,
  class_weight="balanced", random_state=42, n_jobs=-1)` -- all other
  hyperparameters left at sklearn 1.9.1 defaults. `class_weight="balanced"`
  chosen (over `"balanced_subsample"`) as the closer RF analogue to LR's
  `class_weight="balanced"`, both computed from the fold's own TRAIN `y` at
  `.fit()` time. No hyperparameter tuning performed.
- `DummyClassifier(strategy="most_frequent")` naive baseline, refit
  independently in this notebook (same construction as LR's).
- New fold-for-fold cross-check against the LR run's own saved
  `fold_metrics.csv` (`n_train`, `n_test`, `train_preictal_count`,
  `train_interictal_count` compared per fold) -- goes beyond what the LR
  notebook itself checked, to positively confirm this is an
  apples-to-apples comparison.
- Feature-importance summary (`feature_importances_`, the RF analogue of
  LR's standardized coefficients) with a rank-stability metric (fraction of
  folds where a feature lands in that fold's own top-5).
- A TRAIN-accuracy-vs-TEST-accuracy overfitting diagnostic (Section 23.4.6)
  not present in the LR notebook, added specifically to check for RF's
  known tendency to overfit with default (unpruned) tree depth.
- Section reading and combining `outputs/modeling/logistic_loso_binary/overall_horizon_summary.csv`
  and `patient_horizon_summary.csv` (the LR run's actual saved files, not
  hardcoded numbers) to build the LR vs RF comparison tables.

## 25.5 Execution status

**Actually executed**, not just written: `python -m jupyter nbconvert
--to notebook --execute --inplace EEG_random_forest_loso_binary.ipynb`,
full run, `ExecutePreprocessor.timeout=1200`. First attempt hit a
`KeyError: 'n_test'` in the new LR-fold-cross-check cell (the LR
`fold_metrics.csv` has `n_test_preictal`/`n_test_interictal`, not a
combined `n_test` column) -- fixed by deriving `n_test` as their sum before
merging, then re-executed successfully.

Final run: **0 errors** (confirmed by programmatically scanning every code
cell's outputs for `output_type == "error"` -- none found).

Folds expected: 57 (19 eligible seizures x 3 horizons: chb12 5, chb24 14).
Folds successfully built, fit, and validated: **57/57**
(`n_folds_built == 57` asserted in-notebook via `assert n_folds_built ==
57`, and confirmed in the saved `experiment_config.json`:
`"n_folds_total": 57`).

## 25.6 Validation

All of the following were verified by reading the actual executed
notebook's cell outputs and the actual saved files (not assumed):

- The pre-existing 9 leakage checks in `validate_loso_fold` (TRAIN/TEST
  disjoint, held-out seizure's PREICTAL never in TRAIN, scaler
  `n_samples_seen_`/mean matches TRAIN-only recomputation, exactly one
  patient per fold, feature order matches `FEATURE_COLS`, only
  PREICTAL/INTERICTAL rows, no seizure-overlap rows, non-null chronological
  metadata) ran for every one of the 57 folds with no assertion failure.
- `predictions_df` passed `validate_predictions_df()` (required columns
  present; `y_true`/`y_pred` in {0,1}; `y_prob` in [0,1]; no NaNs).
- Cross-check against `outputs/loso_fold_manifest.parquet`: all 57 folds'
  `n_train`/`n_test`/`train_preictal_count`/`train_interictal_count` match
  exactly.
- New cross-check against the LR run's own `fold_metrics.csv`: all 57
  folds' TRAIN/TEST composition matches the LR run exactly -- confirmed the
  two experiments evaluate on identical data.
- Pre-existing outputs (`labels_binary_preictal.parquet`,
  `features_patient_scaled.parquet`, `loso_fold_manifest.parquet`,
  both `*_forecasting.parquet` files, and every file under
  `outputs/modeling/logistic_loso_binary/`) asserted to still exist,
  unmodified, both before and after the run.
- Sanity check: RF's predicted-positive rate on TEST (49.6% at H=5, 71.8%
  at H=15, 79.1% at H=30) is not degenerate (not <2% or >98%) -- not
  repeating the earlier 4-class TCN's majority-class collapse
  (Section 18.1).

No check failed. No workaround or leniency was applied to any assertion.

## 25.7 Results

Exact numbers, read from the saved CSV files after execution (not
recomputed, not estimated):

**Random Forest, pooled overall (`overall_horizon_summary.csv`):**

```text
H= 5min: sensitivity=0.8421 (16/19), FA/hour=16.886, AUC-PR=0.5287
H=15min: sensitivity=0.9474 (18/19), FA/hour=18.323, AUC-PR=0.7314
H=30min: sensitivity=0.9474 (18/19), FA/hour=15.808, AUC-PR=0.7680
```

**Random Forest, per patient (`patient_horizon_summary.csv`):**

```text
chb12 (5/5 eligible, 0 TEST interictal epochs at every horizon):
  H=5:  sensitivity=1.0, FA/hour=NaN, AUC-PR=NaN
  H=15: sensitivity=1.0, FA/hour=NaN, AUC-PR=NaN
  H=30: sensitivity=1.0, FA/hour=NaN, AUC-PR=NaN
chb24 (14 eligible):
  H=5:  sensitivity=0.7857 (11/14), FA/hour=16.886, AUC-PR=0.2742
  H=15: sensitivity=0.9286 (13/14), FA/hour=18.323, AUC-PR=0.5063
  H=30: sensitivity=0.9286 (13/14), FA/hour=15.808, AUC-PR=0.5736
```

**LR vs RF, pooled overall (both from each run's own saved
`overall_horizon_summary.csv`):**

```text
Horizon | Model | Sensitivity | Detected/Eligible | FA/hour | AUC-PR
5 min   | LR    | 0.9474      | 18/19              | 13.653  | 0.5358
5 min   | RF    | 0.8421      | 16/19              | 16.886  | 0.5287
15 min  | LR    | 0.9474      | 18/19              | 13.293  | 0.6505
15 min  | RF    | 0.9474      | 18/19              | 18.323  | 0.7314
30 min  | LR    | 0.9474      | 18/19              | 12.575  | 0.7364
30 min  | RF    | 0.9474      | 18/19              | 15.808  | 0.7680
```

**Overfitting diagnostic (RandomForest, mean TRAIN accuracy vs pooled TEST
accuracy):**

```text
chb12: H=5 1.000 vs 1.000 (gap 0.000); H=15 0.997 vs 0.983 (gap 0.014); H=30 0.997 vs 0.962 (gap 0.035)
chb24: H=5 0.996 vs 0.504 (gap 0.492); H=15 1.000 vs 0.465 (gap 0.535); H=30 1.000 vs 0.565 (gap 0.435)
```

**Feature importance, pooled across all 57 folds (top 4 of 14):**
`entropy` 0.1144, `rel_beta` 0.1131, `beta` 0.1080, `delta_beta_ratio`
0.0973 (most rank-stable, top-5 in 94.7% of folds); `std`/`var`/`rms` never
appear in any fold's top-5.

## 25.8 Limitations / warnings

- CHB12's 0-TEST-interictal structural gap (first surfaced in Section
  20.5 for LOSO fold construction generally) applies identically to RF:
  FA/hour and AUC-PR are genuinely undefined (NaN, not 0, not omitted) for
  CHB12 at every horizon, for both models. Every pooled FA/hour and AUC-PR
  number reported above is therefore driven entirely by CHB24's 14 folds.
- RF shows **worse** FA/hour than LR at every horizon where FA/hour is
  measurable (+3.2 to +5.0 alarms/hour) -- Random Forest does NOT reduce
  false alarms in this experiment; this is a genuine negative result, not
  omitted or softened.
- RF is **less sensitive** than LR at H=5min (0.842 vs 0.947 -- misses 2
  more of the 19 eligible seizures).
- Confirmed overfitting: CHB24 TRAIN accuracy 0.996-1.000 vs pooled TEST
  accuracy 0.465-0.565 (gap up to 0.535), the expected consequence of
  `max_depth=None` (unpruned trees) on a baseline that deliberately
  performed no hyperparameter tuning. This is a real limitation of the
  configuration used, not fixed in this task per its explicit scope
  ("Do NOT perform hyperparameter tuning").
- AUC-PR gains for RF over LR are modest (max +0.081, at H=15) and not
  monotonic with horizon (H=5 is actually slightly negative, -0.007) --
  not strong evidence that Random Forest is a materially better classifier
  for this qEEG feature representation.
- Sample size remains 2 patients / 19 eligible seizures total across all
  horizons combined -- every number above (LR's and RF's alike) is
  statistically fragile at the per-fold and per-patient level; no
  significance testing was performed on the LR-vs-RF deltas.
- H=30min: 19/19 folds have TRAIN PREICTAL prevalence > 0.5, so
  `dummy_most_frequent` alone reaches sensitivity=1.0 with low FA/hour
  (3.23/hour) at that horizon -- a caveat already established for LR
  (Section 22.2) that applies unchanged to RF's H=30 numbers.

## 25.9 Current pipeline after this task

```text
CHB12 + CHB24
  -> qEEG features (14 columns, EEG_binary_preictal_labeling.ipynb's source tables)
  -> binary PREICTAL / INTERICTAL labeling (H = 5 / 15 / 30 min, >=30 min postictal exclusion)
  -> Leave-One-Seizure-Out fold construction (57 folds: 19 eligible seizures x 3 horizons)
  -> patient-specific StandardScaler, fit on TRAIN only, per fold
  -> seizure-prediction metrics (event-level: sensitivity, FA/hour, time-in-warning;
     epoch-level: accuracy, precision/recall/F1, AUC-PR)
  -> TWO estimators now evaluated on these identical 57 folds:
       (a) Logistic Regression (class_weight="balanced", C=default) -- outputs/modeling/logistic_loso_binary/
       (b) Random Forest (n_estimators=100, class_weight="balanced", default depth) -- outputs/modeling/random_forest_loso_binary/
  -> LR vs RF comparison table (outputs/modeling/random_forest_loso_binary/lr_vs_rf_comparison_overall.csv / _by_patient.csv)
  -> TCN on these LOSO folds: NOT YET STARTED
```

The old 4-class TCN notebooks (`EEG_TCN_seizure_forecasting.ipynb`,
`EEG_TCN_state_deviation_forecasting.ipynb`) remain untouched, separate
project history (Section 18.1) -- not part of this pipeline.

## 25.10 Updated status table

| Component | Status |
|---|---|
| Binary PREICTAL/INTERICTAL labeling (5/15/30 min) | COMPLETE (Section 18) |
| Patient-specific TRAIN-only normalization | COMPLETE (Section 19) |
| LOSO evaluation splitting (57 folds) | COMPLETE (Section 20) |
| Seizure-prediction metric framework | COMPLETE (Section 22.1) |
| Logistic Regression LOSO baseline | COMPLETE (Section 22.2) |
| **Random Forest LOSO baseline** | **COMPLETE (this task, Section 23 / 25)** |
| LR vs RF comparison | COMPLETE (Section 23.4 / 25.7) |
| RF overfitting fix (depth/leaf tuning) | NOT STARTED (identified, not addressed -- out of this task's scope) |
| TCN on binary LOSO folds | NOT STARTED |
| LR vs RF vs TCN 3-way comparison | NOT STARTED (only 2 of 3 estimators exist) |
| Hyperparameter tuning (either model) | NOT STARTED (deliberately, both are first baselines) |
| Statistical significance testing on LR-vs-RF deltas | NOT STARTED |
| Expansion beyond chb12/chb24 | NOT STARTED |
| Channel-wise representation | NOT STARTED |
| Preprocessing V1 final re-audit | NOT STARTED / STILL "IN PROGRESS" (Section 6, unchanged by this task) |

## 25.11 Exact next step

**Recommended next step: implement a TCN baseline on these same 57 binary
LOSO folds**, using the identical fold construction, normalization, and
metric functions reused verbatim by both the LR and RF notebooks (the same
reuse pattern that made this task's LR-vs-RF comparison fair applies
directly to a TCN version).

Why this is next in the dependency order: the task's own framing ("LR vs RF
vs TCN") and Section 21/24's "STILL PENDING" list both name TCN as the
remaining piece needed to complete the three-way baseline comparison on the
binary task; the LOSO fold/metric infrastructure it depends on is already
built, validated, and twice reused (Sections 20-23) so no further
infrastructure work blocks it. Hyperparameter tuning of RF (to address the
overfitting found in Section 25.8) is a reasonable alternative next step,
but is lower priority than TCN because the task scope for both LR and RF
was explicitly "no tuning" -- tuning either model before a TCN baseline
exists would front-load effort into classical ML before the more
architecturally distinct comparison point is even established.

---

# 26. TCN LOSO BASELINE (BINARY, TEMPORAL HISTORY MODEL)

Added 2026-09-14 (completion sprint), after implementation, execution
(`jupyter nbconvert --execute`, clean run, no errors), and inspection of the
actual saved outputs.

Status: `TCN IMPLEMENTED AND EXECUTED ON ALL 57 ATTEMPTED LOSO FOLDS; 48/57
PRODUCED >=1 VALID TEST SEQUENCE AND WERE EVALUATED (16/19 ELIGIBLE
SEIZURES PER HORIZON); 9/57 SKIPPED FOR DOCUMENTED, REPORTED REASONS
(INSUFFICIENT SAME-SPLIT CONTIGUOUS HISTORY), NOT SILENTLY SUBSTITUTED.
OUTPUTS SAVED AND INSPECTED. A REAL, MATERIAL LIMITATION WAS DISCOVERED AND
IS DOCUMENTED, NOT HIDDEN (Section 26.6).`

## 26.1 Scope and reuse

New notebook: `EEG_TCN_loso_binary.ipynb`. Independent of, and does not
read or modify, the historical 4-class TCN notebooks
(`EEG_TCN_seizure_forecasting.ipynb`, `EEG_TCN_state_deviation_forecasting.ipynb`)
-- those remain historical-only (Section 18.1). Reads
`outputs/labels_binary_preictal.parquet` read-only, same as LR/RF.
Fold-construction functions (`compute_seizure_eligibility`,
`assign_fold_context`, `fit_patient_scalers`, `transform_with_patient_scalers`,
`build_loso_fold`, `validate_loso_fold`) and metric functions
(`fold_seizure_event_metrics`, `fold_epoch_metrics`, `pool_epoch_metrics`,
`pool_event_metrics`) copied verbatim from `EEG_logistic_loso_binary.ipynb`.

## 26.2 Sequence construction (new for this notebook)

**Metadata actually inspected before designing this** (verified
programmatically in-notebook, not assumed): `epoch_idx` is contiguous with
no gaps within every one of the 17 recordings.

**History length**: `SEQUENCE_LENGTH = 10` epochs (5 minutes), referencing
the historical 4-class TCN's `SEQUENCE_LENGTH=10` as a starting point (its
leakage/splitting/scaling methodology was NOT reused, only the epoch-count
magnitude). A feasibility check run against the real 57 folds found 48/57
folds still produce >=1 valid TEST sequence at length 10 (vs 54/57 at
length 5); length 10 was kept for a genuinely useful 5-minute temporal
window, with the reduced coverage reported explicitly rather than silently
switching to a shorter, higher-coverage length.

**Rule enforced for every sequence (stricter than the historical TCN's, per
explicit task requirement)**: all `SEQUENCE_LENGTH` consecutive epochs in a
window must (1) belong to the same `recording_id`, (2) have strictly
contiguous `epoch_idx`, and (3) **all belong to the SAME fold split** (all
`train_idx`, or all `test_idx`) -- a sequence never crosses a TRAIN/TEST
boundary, and an excluded/seizure-overlapping epoch anywhere in the window
breaks it (since such epochs belong to neither split). This is materially
stricter than the historical TCN (whose single recording-level TRAIN/VAL/
TEST split made this trivial); under the LOSO folds here, TRAIN and TEST
epochs can come from the SAME recording (project_state.md Section 20.3), so
this is a genuinely new construction.

`verify_fold_sequences` independently re-derives, for every fold (not
sampled), that: every TRAIN window's epochs are a subset of `train_idx`,
every TEST window's epochs are a subset of `test_idx`, TRAIN and TEST
window epoch-sets are disjoint, and no held-out seizure's PREICTAL epoch
ever appears in a TRAIN window.

## 26.3 Architecture and training

`TinyTCNBinary`: 3 causal, dilated `Conv1d` blocks (dilations 1/2/4,
`hidden=16`, `kernel_size=3`, left-padded so output at timestep `t` is a
function of input `<= t` only -- no future information reaches the
representation, by construction), single linear output logit
(`sigmoid(logit) = P(PREICTAL)`). A fresh implementation for this task,
architecturally inspired by (not copied from) the historical TCN's
`TinyTCN`/`CausalConv1d`.

**Training** (fixed for every fold, no per-fold tuning, no TEST-data
tuning): Adam, `lr=1e-3`; `BCEWithLogitsLoss` with `pos_weight =
n_train_neg / n_train_pos` computed from the actual sub-TRAIN sequences
passed to `.fit()` (TCN's analogue of LR's/RF's `class_weight="balanced"`);
batch size `min(32, n_subtrain)`; up to 60 epochs with early stopping
(patience 10, min-delta 1e-4) on a TRAIN-only validation split, or a fixed
30 epochs with no early stopping when no validation split was constructible
(documented per-fold in `fold_sequence_diagnostics.csv`); `torch.manual_seed(42)`
/ `np.random.seed(42)` reset before every fold. Decision threshold fixed at
0.5, matching LR/RF.

**TRAIN-only validation split** (Section 7 of the notebook): recording-
level holdout (smallest recordings assigned to validation first, targeting
~20% of TRAIN sequences, always leaving >=1 recording for training) when
TRAIN sequences span >=2 recordings; a chronological last-20%-with-gap
fallback (dropping boundary sequences to prevent window overlap) when only
1 recording contributes TRAIN sequences. Falls back further to "no
validation, fixed 30 epochs" when even that split cannot produce a usable
2-class sub-TRAIN + non-empty validation set. 40/48 evaluated folds used
early stopping with a real validation split; the rest used the fixed-epoch
fallback (both documented per-fold, not hidden behind one aggregate number).

## 26.4 Execution status and fold coverage

Executed via `jupyter nbconvert --to notebook --execute --inplace`, full
run, 0 errors (confirmed by scanning every code cell's outputs for
`output_type == "error"`).

- **Folds attempted**: 57/57 (matches LR/RF exactly -- same underlying LOSO
  construction, independently cross-checked in-notebook against
  `outputs/loso_fold_manifest.parquet` AND against the LR run's own saved
  `fold_metrics.csv`, both at the epoch level, both passing exactly).
- **Folds evaluated** (>=1 valid TEST sequence, TCN trained and predicted):
  **48/57** (16/19 eligible seizures at each of the 3 horizons).
- **Folds skipped** (0 valid TEST sequences under the Section 26.2 rule,
  recorded with reason, never silently substituted): **9/57** -- the SAME 3
  seizures at every horizon: `chb_s12_r23_sz0` (chb12), `chb_s24_r01_sz1`
  and `chb_s24_r03_sz0` (chb24). Saved in
  `outputs/modeling/tcn_loso_binary/skipped_folds.csv`.

## 26.5 Leakage / validation results

All of the following passed for every fold (not sampled): the pre-existing
9 `validate_loso_fold` checks (identical to LR/RF); `verify_fold_sequences`
(TRAIN/TEST window epoch-sets subsets of their respective split and
mutually disjoint; held-out seizure's PREICTAL epochs never in a TRAIN
window; within-window `epoch_idx` strictly contiguous); the new epoch-level
cross-check against `loso_fold_manifest.parquet` (57/57 exact match) and
against the LR run's own `fold_metrics.csv` (57/57 exact match, confirming
LR, RF, and TCN all evaluate the identical underlying LOSO folds before
TCN's sequence restriction). `predictions_df` passed `validate_predictions_df()`.
Pre-existing outputs (including all of `outputs/modeling/logistic_loso_binary/`
and `outputs/modeling/random_forest_loso_binary/`) verified unmodified
(timestamps unchanged) before and after this run.

## 26.6 Results and a critical, honestly-reported limitation

**Pooled overall (evaluated folds only, `overall_horizon_summary.csv`):**

```text
H= 5min: sensitivity=0.938 (15/16), FA/hour=3.158, AUC-PR=0.363
H=15min: sensitivity=0.938 (15/16), FA/hour=3.158, AUC-PR=0.550
H=30min: sensitivity=0.938 (15/16), FA/hour=3.158, AUC-PR=0.794
```

**[CRITICAL CAVEAT -- discovered during this task's own sanity checks, not
glossed over]**: TCN's TEST predicted-positive rate is 1.000 at H=5, 0.978
at H=15, and 0.987 at H=30 -- the TCN predicts PREICTAL on almost every
TEST sequence at EVERY horizon (flagged as degenerate, >98% positive, at
H=5 and H=30 by the SAME check LR/RF are held to). CHB24's confusion
matrices show **TN=0 at every horizon** -- 100% of CHB24's interictal TEST
sequences are false positives. The apparently low pooled FA/hour (3.16/hour,
well below LR's 12.6-13.7 and RF's 15.8-18.3) is an **artifact of the
alarm-event-merging convention** (Section 22.1): a near-constant positive
prediction collapses into very few countable "alarm events," not genuine
specificity -- the same mechanism already documented for the H=30
`dummy_most_frequent` baseline (Section 22.2), now present in the TCN's own
model output at every horizon. **The fixed-threshold (0.5) sensitivity/
FA-hour/precision/accuracy numbers above must NOT be read as "TCN has fewer
false alarms than LR/RF."** AUC-PR (threshold-independent, rank-based) is
less affected and may still carry real signal -- see Section 27.

Likely cause: `pos_weight` for the most-imbalanced folds (e.g. CHB24 H=5,
~266 negative vs ~10-11 positive sub-train sequences) is very large
(~24-27x); early stopping fires quickly (mean 14.9 epochs trained); this
compact architecture with a fixed `lr=1e-3` and 0.5 threshold was not
calibrated to handle that combination well. A real limitation of this
specific baseline configuration -- **not fixed in this sprint** (threshold/
hyperparameter tuning was explicitly out of scope) -- and the most
important open item before any future TCN claim (Section 29.15).

**Per-patient** (`patient_horizon_summary.csv`): CHB12 (4/4 evaluable
seizures -- 1 of its 5 skipped, Section 26.4) reaches sensitivity=1.0 with
FA/hour and AUC-PR undefined (NaN), same structural reason as LR/RF. CHB24
(11-13/12 evaluable depending on horizon) AUC-PR: 0.064 (H=5, severely
degraded by the collapse above), 0.339 (H=15), 0.608 (H=30, TCN's best
single number in the whole 3-way comparison, Section 27).

**Overfitting diagnostic** (mean fold TRAIN accuracy vs pooled TEST
accuracy): CHB24 shows near-ZERO gap at every horizon (e.g. H=5: TRAIN
0.040 vs TEST 0.040) -- because both TRAIN and TEST are equally saturated
by the same near-all-positive collapse described above, not because the
model generalizes well. CHB12 shows a large *negative* gap at H=5/H=15
(TRAIN accuracy far below TEST accuracy, e.g. H=5: TRAIN 0.097 vs TEST
1.000) -- an artifact of CHB12's TEST sets containing only PREICTAL epochs
(0 TEST interictal, Section 20.5), so a collapsed all-positive model scores
perfectly on TEST while scoring poorly on TRAIN's more balanced mix. Unlike
RF's overfitting (real train-vs-test generalization gap, Section 23.4.6),
this pattern is a symptom of the SAME prediction-collapse issue above, not
independent evidence of classic overfitting.

## 26.7 Outputs

`outputs/modeling/tcn_loso_binary/` -- `predictions.parquet` / `.csv`
(sequence-level, both `tcn` and `dummy_most_frequent`, evaluated folds
only), `fold_metrics.csv`, `patient_horizon_summary.csv`,
`overall_horizon_summary.csv`, `fold_sequence_diagnostics.csv` (per-fold
sequence counts, validation method used, epochs trained -- ALL 57 attempted
folds, including skipped ones), `skipped_folds.csv` (the 9 skipped folds
with reasons), `lr_vs_rf_vs_tcn_comparison_overall.csv` /
`_by_patient.csv`, `experiment_config.json`, and `plots/` (PR curves,
confusion matrices, probability distributions). `outputs/modeling/
logistic_loso_binary/` and `outputs/modeling/random_forest_loso_binary/`
confirmed untouched.

## 26.8 Explicitly NOT implemented / NOT fixed in this task

- The H=5/H=30 near-all-positive prediction collapse (Section 26.6) --
  identified and quantified, not fixed. No threshold recalibration, no
  `pos_weight` capping, no architecture change was attempted (all would
  constitute tuning against knowledge gained from this run).
- Any hyperparameter search (architecture size, learning rate, batch size,
  epoch budget, patience -- all fixed, all documented, Section 26.3).
- Channel-wise or raw-EEG input representation (still the 14 qEEG features,
  per explicit task scope).
- Recovering the 9 skipped folds' TEST evaluability (would require either a
  shorter `SEQUENCE_LENGTH` or a relaxed same-split rule -- a methodology
  change, out of scope here and deliberately not made silently).
- Expansion beyond CHB12/CHB24; statistical significance testing.

---

# 27. THREE-WAY COMPARISON: LOGISTIC REGRESSION vs RANDOM FOREST vs TCN

Added 2026-09-14. All numbers read directly from each model's own saved
`overall_horizon_summary.csv` / `patient_horizon_summary.csv` -- never
hardcoded from a prior report. Source: `outputs/modeling/tcn_loso_binary/
lr_vs_rf_vs_tcn_comparison_overall.csv` / `_by_patient.csv`.

## 27.1 Pooled overall, by horizon

```text
Horizon | Model               | Sensitivity | Det/Elig | FA/hour | AUC-PR | Precision | Recall | F1
5 min   | Logistic Regression | 0.947       | 18/19    | 13.653  | 0.536  | 0.348     | 0.682  | 0.461
5 min   | Random Forest       | 0.842       | 16/19    | 16.886  | 0.529  | 0.388     | 0.571  | 0.462
5 min   | TCN                 | 0.938       | 15/16*   | 3.158†  | 0.363  | 0.053†    | 1.000  | 0.101†
15 min  | Logistic Regression | 0.947       | 18/19    | 13.293  | 0.650  | 0.564     | 0.784  | 0.656
15 min  | Random Forest       | 0.947       | 18/19    | 18.323  | 0.731  | 0.581     | 0.730  | 0.647
15 min  | TCN                 | 0.938       | 15/16*   | 3.158†  | 0.550  | 0.511†    | 0.959  | 0.667
30 min  | Logistic Regression | 0.947       | 18/19    | 12.575  | 0.736  | 0.685     | 0.787  | 0.732
30 min  | Random Forest       | 0.947       | 18/19    | 15.808  | 0.768  | 0.702     | 0.809  | 0.752
30 min  | TCN                 | 0.938       | 15/16*   | 3.158†  | 0.794  | 0.698     | 0.981  | 0.815
```

`*` TCN's denominator is 16 eligible seizures per horizon (not 19) --
3 seizures per horizon could not produce a valid TEST sequence (Section
26.4), an intrinsic coverage limitation of the sequence-based approach, not
a modeling choice. `†` See Section 26.6 -- TCN's fixed-threshold FA/hour,
precision, and F1 at H=5 (and, to a lesser extent, H=15) are artifacts of a
near-all-positive prediction collapse, NOT genuine performance; AUC-PR is
the more trustworthy TCN number at each horizon.

## 27.2 Scientific interpretation (from the notebook's own Section 16, not hardcoded)

1. **Does RF outperform LR?** No clear win: RF's AUC-PR is worse at H=5
   (-0.007), better at H=15 (+0.081) and H=30 (+0.032); RF's FA/hour is
   worse than LR's at every horizon.
2. **Does TCN outperform LR?** No -- TCN's AUC-PR is worse than LR's at
   H=5 (0.363 vs 0.536) and H=15 (0.550 vs 0.650), better at H=30 (0.794 vs
   0.736). Given the Section 26.6 caveat, this is a mixed, not a clear,
   result.
3. **Does TCN outperform RF?** Same pattern: worse at H=5/H=15, better at
   H=30 (0.794 vs 0.768).
4. **Which horizon appears strongest?** H=30 for all three models (best
   AUC-PR for each individually: LR 0.736, RF 0.768, TCN 0.794).
5. **Which model gives the best AUC-PR per horizon?** H=5: LR (0.536).
   H=15: RF (0.731). H=30: TCN (0.794) -- but see caveat below.
6. **Which gives the best sensitivity/false-alarm tradeoff?** At face
   value TCN looks best (FA/hour 3.16 vs LR's 12.6-13.7 and RF's
   15.8-18.3) -- **this is the artifact from Section 26.6, not a genuine
   result**; among LR and RF (which do not have this artifact), LR has
   consistently lower FA/hour than RF at comparable sensitivity.
7. **Are results dominated by CHB24?** Yes, for all three models -- CHB12
   contributes sensitivity only; FA/hour and AUC-PR are NaN for CHB12 at
   every horizon for every model, since CHB12 has 0 TEST interictal epochs
   at every horizon (Section 20.5).
8. **Is H=30 still vulnerable to the majority-class/dummy-baseline issue?**
   Yes -- all 19/19 folds have TRAIN PREICTAL prevalence > 0.5 at H=30 for
   every model's fold construction (identical folds); `dummy_most_frequent`
   reaches high sensitivity with low FA/hour at H=30 purely from that
   prevalence, for LR, RF, and TCN's evaluated subset alike.
9. **Does temporal modeling provide measurable benefit?** TCN vs RF AUC-PR
   delta: H=5 -0.166, H=15 -0.181, H=30 +0.026. Given TCN's reduced
   coverage (16/19 not 19/19) and the Section 26.6 threshold-collapse
   issue contaminating its H=5/H=15 fixed-threshold metrics, **this sprint
   does not find clear evidence that explicit temporal modeling improves
   binary seizure forecasting over the static baselines** with this
   architecture/training configuration -- the one AUC-PR win (H=30) is
   suggestive, not conclusive, and needs the calibration issue fixed
   before it can be trusted.
10. **Is the 14-feature qEEG representation likely limiting all three
    models?** Consistent with that hypothesis: all three model families
    (linear, tree-ensemble, temporal-conv) share the identical features and
    folds, and none shows a large, unambiguous, horizon-consistent win over
    the others -- more consistent with a shared representational ceiling
    than with any one estimator being clearly superior.
11. **Are there signs of overfitting?** RF: yes, confirmed and material
    (CHB24 TRAIN accuracy ~0.996-1.0 vs TEST ~0.46-0.56, Section 23.4.6).
    TCN: the TRAIN-vs-TEST accuracy gap is small or even negative, but this
    reflects the Section 26.6 prediction collapse (both TRAIN and TEST
    scored by an almost-constant predictor), not evidence of good
    generalization -- a different failure mode, not an absence of one.
12. **What conclusions are scientifically defensible with only two
    patients?** Very limited ones. 2 patients, 19 eligible seizures per
    horizon (16 for TCN), no significance testing performed on any
    pairwise model difference. None of the LR/RF/TCN differences above
    should be read as a generalizable claim about which model family is
    "better" for seizure forecasting -- descriptive results on this
    specific sample only.

---

# 28. FINAL CORE PIPELINE AUDIT (Phase 6)

Added 2026-09-14. Distinguishes (A) the CORE MODELING PIPELINE this sprint
targeted from (B) PAPER-EXPANSION WORK still outside its scope. Status
values: COMPLETE, PARTIAL, BLOCKED, NOT STARTED, HISTORICAL ONLY.

## 28.A Core modeling pipeline (this sprint's target)

| Stage | Status | Evidence |
|---|---|---|
| EDF -> qEEG feature extraction (CHB12/CHB24 specific) | COMPLETE | `EEG_CHB12_preprocessing.ipynb`, `EEG_CHB24_preprocessing.ipynb`, `outputs/features_chb12_forecasting.parquet` / `features_chb24_forecasting.parquet`, used unmodified throughout |
| Binary PREICTAL/INTERICTAL labeling | COMPLETE | Section 18, `outputs/labels_binary_preictal.parquet` |
| >=30 min postictal exclusion | COMPLETE | Embedded in labeling, Section 18.3 |
| Horizons (5/15/30 min) | COMPLETE | All 3 horizons run through every stage below |
| Leave-One-Seizure-Out fold construction | COMPLETE | Section 20, 57/57 folds, 9 checks each; independently re-verified inside LR (Section 22.2), RF (Section 23.1), and TCN (Section 26.5) |
| Patient-specific TRAIN-only normalization | COMPLETE | Section 19, reused verbatim in every model notebook |
| Seizure-prediction metric framework | COMPLETE | Section 22.1, reused verbatim (identical code) by LR, RF, TCN |
| Logistic Regression on LOSO folds | COMPLETE | Section 22.2, 57/57 folds |
| Random Forest on LOSO folds | COMPLETE | Section 23, 57/57 folds |
| TCN on LOSO folds | **COMPLETE, WITH A DOCUMENTED LIMITATION** | Section 26, 48/57 folds evaluated (9 skipped for reported reasons); prediction-collapse issue at H=5/H=30 identified, not fixed |
| LR vs RF vs TCN comparison | COMPLETE | Section 27 |
| Scientific interpretation (12 questions) | COMPLETE | Section 27.2 |

**None of the above is "falsely complete"**: every COMPLETE row was
implemented, executed end-to-end with zero errors, had its outputs saved
and then actually inspected (not assumed from print statements), passed its
leakage/validation checks, and has its results recorded with real numbers
(including a real, currently-unresolved limitation for TCN).

## 28.B Paper-expansion work (deliberately out of scope this sprint)

| Item | Status |
|---|---|
| TCN prediction-collapse / threshold-calibration fix | NOT STARTED (identified in Section 26.6; recommended next step, Section 29.15) |
| Hyperparameter tuning (LR `C`, RF depth/leaf-size, TCN architecture/lr/threshold) | NOT STARTED (deliberately, for all three -- first baselines) |
| Statistical significance testing on any pairwise model delta | NOT STARTED |
| Expansion beyond CHB12/CHB24 (10+ patients) | NOT STARTED |
| Channel-wise / raw-EEG feature redesign | NOT STARTED |
| CNN / EEGNet / Transformers / Chronos | NOT STARTED |
| Sleep-stage prediction | NOT STARTED (Section 3.2 -- no verified hypnogram exists at all) |
| New labels / new horizons | NOT STARTED |
| Preprocessing V1 final cross-dataset re-audit (REST/SLEEP channel handling, filtering validation) | PARTIAL / NOT RE-AUDITED (Section 6 still "IN PROGRESS"; does not block the CHB-only binary pipeline above, which has its own independently-verified preprocessing via the CHB12/CHB24 notebooks) |
| Old 4-class TCN notebooks | HISTORICAL ONLY (Section 18.1, untouched, not part of this pipeline) |

**The full research project is NOT being called complete.** The 3-model
core experiment (A) is complete by the strict definition used throughout
this document (implemented, executed, saved, inspected, validated,
reported) -- the paper-expansion items in (B), especially the TCN
calibration issue, remain open.

---

# 29. TASK RECORD -- COMPLETION SPRINT: RF (confirmed) + TCN + 3-WAY COMPARISON + PIPELINE AUDIT (2026-09-14)

Mandatory structured record for this sprint's task, per the supervisor's
explicit reporting requirement. Sections 23/25 (RF, already complete
before this sprint, re-verified as still valid and untouched) and 26-28
(TCN, comparison, audit -- new this sprint) hold full narrative detail;
this section is the checklist-format summary of THIS sprint specifically.

## 29.1 Task completed

Sprint goal: bring the 2-patient binary LOSO pipeline to LR + RF + TCN, all
on identical folds/methodology, with a 3-way comparison and pipeline audit.

Status: **RF -- already COMPLETE from a prior session, re-verified
untouched and still valid** (file timestamps checked: unchanged). **TCN --
newly implemented and COMPLETE this sprint, WITH a real, documented
limitation** (Section 26.6 prediction-collapse issue) that is surfaced, not
hidden, and explicitly left unresolved per the sprint's own
no-tuning/no-recalibration scope. **3-way comparison and scientific
interpretation -- COMPLETE.** **Pipeline audit -- COMPLETE** (Section 28).

## 29.2 Files created (this sprint)

- `EEG_TCN_loso_binary.ipynb` (repo root, new) -- 35 cells.
- `outputs/modeling/tcn_loso_binary/` (new directory): `predictions.parquet`,
  `predictions.csv`, `fold_metrics.csv`, `patient_horizon_summary.csv`,
  `overall_horizon_summary.csv`, `fold_sequence_diagnostics.csv`,
  `skipped_folds.csv`, `lr_vs_rf_vs_tcn_comparison_overall.csv`,
  `lr_vs_rf_vs_tcn_comparison_by_patient.csv`, `experiment_config.json`,
  `plots/` (`pr_curves_overall_by_horizon.png`, `confusion_matrices_tcn.png`,
  `probability_distributions.png`).

(`EEG_random_forest_loso_binary.ipynb` and `outputs/modeling/
random_forest_loso_binary/` were created in a PRIOR session, Sections
23/25 -- not created this sprint. Verified still present and untouched.)

## 29.3 Files modified

- `.claude/skills/eeg-context/project_state.md` -- appended Sections 26-29
  (this record) and updated the header date. No prior section rewritten or
  deleted.

No other existing file was modified. Verified by direct inspection: every
file under `outputs/modeling/logistic_loso_binary/` (timestamp Sep 9 16:12)
and `outputs/modeling/random_forest_loso_binary/` (timestamp Sep 14, from
the prior session, unchanged by this sprint) retained its pre-sprint
timestamp after the TCN notebook's execution.

## 29.4 Implementation

Reused verbatim across ALL THREE model notebooks (LR, RF, TCN): fold
construction (`compute_seizure_eligibility`, `assign_fold_context`,
`fit_patient_scalers`, `transform_with_patient_scalers`, `build_loso_fold`,
`validate_loso_fold`) and metrics (`fold_seizure_event_metrics`,
`fold_epoch_metrics`, `pool_epoch_metrics`, `pool_event_metrics`) --
byte-for-byte identical code, independently cross-checked this sprint
(Section 26.5) to confirm TCN evaluates the exact same underlying folds as
LR and RF.

New this sprint (TCN-specific): sequence construction under a strict
same-split/same-recording/contiguous rule (Section 26.2);
`verify_fold_sequences` leakage re-verification; `TinyTCNBinary` causal
dilated-Conv1d architecture (Section 26.3); TRAIN-only validation-split
function with a recording-level primary strategy and chronological-gap
fallback (Section 26.3); per-fold training loop with early stopping;
fold-coverage accounting and reporting (skipped folds recorded, not
hidden); 3-way comparison table construction reading LR's, RF's, and TCN's
own saved CSVs.

## 29.5 Model configurations

- **LR** (unchanged from prior session): `LogisticRegression(class_weight=
  "balanced", random_state=42, solver="lbfgs", max_iter=1000)`.
- **RF** (unchanged from prior session): `RandomForestClassifier(
  n_estimators=100, class_weight="balanced", random_state=42, n_jobs=-1)`.
- **TCN** (new): `TinyTCNBinary(hidden=16, kernel_size=3, dilations=(1,2,4))`;
  Adam `lr=1e-3`; `BCEWithLogitsLoss(pos_weight=n_train_neg/n_train_pos)`;
  batch size `min(32, n_subtrain)`; up to 60 epochs, early-stopping patience
  10 (or fixed 30 epochs, no early stopping, when no validation split was
  constructible); `SEQUENCE_LENGTH=10` epochs (5 min); `random_state=42`;
  decision threshold 0.5 (all three models). No hyperparameter tuning for
  any of the three models.

## 29.6 Execution status

All three notebooks **actually executed** via `jupyter nbconvert --execute
--inplace`, confirmed by scanning every code cell's outputs for
`output_type == "error"` (none found, for RF or TCN -- LR's prior execution
was likewise previously verified error-free).

## 29.7 Number of expected and successful folds

| Model | Folds attempted | Folds evaluated | Notes |
|---|---|---|---|
| LR | 57 | 57 | epoch-level, no sequence-history requirement |
| RF | 57 | 57 | epoch-level, no sequence-history requirement |
| TCN | 57 | **48** | 9 skipped (same 3 seizures x 3 horizons) for documented, reported reasons -- NOT silently substituted or padded |

## 29.8 Leakage/validation checks

LR and RF: the pre-existing 9 `validate_loso_fold` checks, passed 57/57
each (re-confirmed present and unchanged this sprint). TCN: the same 9
checks (reused verbatim) PLUS `verify_fold_sequences` (TRAIN/TEST window
epoch-sets are subsets of their split and mutually disjoint; held-out
seizure's PREICTAL epochs never in a TRAIN window; contiguous `epoch_idx`
within every window) run for every one of the 57 attempted folds, PLUS a
new epoch-level cross-check against both `loso_fold_manifest.parquet` and
the LR run's own `fold_metrics.csv` (57/57 exact match on both). **No check
failed. No workaround or leniency was applied to any assertion.**

## 29.9 Exact results

See Section 23.3/23.7 (RF) and Section 26.6 (TCN) for exact per-model
numbers, and Section 27.1 for the merged 3-way pooled table (read from the
actual saved CSVs, reproduced in full there).

## 29.10 LR vs RF vs TCN comparison

See Section 27 in full (table + 12-question interpretation). Headline:
H=30 is the strongest horizon for all three models; TCN's H=30 AUC-PR
(0.794) is numerically the highest of the three, but TCN's H=5/H=15
fixed-threshold metrics (FA/hour, precision, F1) are contaminated by a
documented near-all-positive prediction collapse (Section 26.6) and should
not be read as genuine improvements. No model shows a large, unambiguous,
horizon-consistent win over the others.

## 29.11 Limitations/warnings

- **TCN prediction collapse (Section 26.6)**: TEST predicted-positive rate
  >=97.8% at every horizon; CHB24 TN=0 at every horizon; the low reported
  FA/hour is an alarm-event-merging artifact, not genuine specificity. The
  single most important open issue from this sprint.
- **TCN's reduced fold coverage**: 48/57 (16/19 eligible seizures per
  horizon), vs LR/RF's full 57/57 (19/19) -- an intrinsic consequence of
  requiring 10 contiguous same-split epochs, reported explicitly in every
  comparison table (never silently padded to look like full coverage).
- CHB12's 0-TEST-interictal structural gap (Section 20.5) applies
  identically to all three models -- FA/hour and AUC-PR are genuinely
  undefined (NaN) for CHB12 at every horizon.
- H=30's majority-baseline caveat (Section 22.2) applies to all three
  models' fold construction (identical folds, identical TRAIN prevalence).
- RF's confirmed overfitting (Section 23.4.6) remains a real, unaddressed
  limitation of that baseline.
- Sample size remains 2 patients / 19 eligible seizures (16 for TCN) --
  no significance testing performed on any pairwise model difference.

## 29.12 Current pipeline

```text
CHB12 + CHB24
  -> qEEG features (14 columns)
  -> binary PREICTAL/INTERICTAL labeling (H=5/15/30 min, >=30 min postictal exclusion)
  -> LOSO fold construction (57 folds: 19 eligible seizures x 3 horizons)
  -> patient-specific StandardScaler, fit on TRAIN only, per fold
  -> seizure-prediction metrics (event-level + epoch-level, identical framework)
  -> THREE estimators now evaluated on these folds:
       (a) Logistic Regression -- outputs/modeling/logistic_loso_binary/ (57/57 folds)
       (b) Random Forest        -- outputs/modeling/random_forest_loso_binary/ (57/57 folds)
       (c) TCN (temporal)       -- outputs/modeling/tcn_loso_binary/ (48/57 folds; sequence-construction limited)
  -> LR vs RF vs TCN comparison (outputs/modeling/tcn_loso_binary/lr_vs_rf_vs_tcn_comparison_*.csv)
  -> Scientific interpretation (Section 27.2)
```

This matches the sprint's target diagram, with TCN's coverage limitation as
the one honest deviation from "all three models see all 57 folds."

## 29.13 Updated status table

| Component | Status |
|---|---|
| Binary labeling, normalization, LOSO, metrics framework | COMPLETE (Sections 18-22) |
| Logistic Regression LOSO baseline | COMPLETE (Section 22.2) |
| Random Forest LOSO baseline | COMPLETE (Section 23/25) |
| **TCN LOSO baseline** | **COMPLETE, with documented prediction-collapse limitation (Section 26)** |
| **LR vs RF vs TCN comparison** | **COMPLETE (Section 27)** |
| **Core pipeline audit** | **COMPLETE (Section 28)** |
| TCN calibration/threshold fix | NOT STARTED (identified, Section 26.6/29.15) |
| RF overfitting fix | NOT STARTED (identified, Section 23.4.6) |
| Hyperparameter tuning (any model) | NOT STARTED (deliberately) |
| Statistical significance testing | NOT STARTED |
| Expansion beyond chb12/chb24 | NOT STARTED |
| Channel-wise / raw-EEG representation | NOT STARTED |
| Preprocessing V1 final cross-dataset re-audit | PARTIAL / STILL "IN PROGRESS" (Section 6, unchanged) |

## 29.14 Remaining work

See Section 28.B (paper-expansion work) in full. Highest-priority items:
(1) TCN prediction-collapse/calibration fix, (2) RF overfitting fix, (3)
statistical significance testing on the LR/RF/TCN deltas before any of
this sprint's comparative claims are used in a paper, (4) the still-open
Preprocessing V1 cross-dataset re-audit (does not block this CHB-only
pipeline but remains open per Section 6).

## 29.15 Exact next step

**Recommended next step: diagnose and fix the TCN's near-all-positive
prediction collapse at H=5/H=30 (Section 26.6)** before drawing any further
conclusion that favors TCN over LR/RF.

Why this is next in the dependency order: it is the single most consequential
open finding from this sprint -- it directly undermines the one horizon
(H=30) where TCN currently looks best, and makes the entire TCN row of the
3-way comparison (Section 27.1) unreliable at fixed threshold. Candidate
fixes (order of likely lowest to highest effort): (a) tune the TCN's
decision threshold using a TRAIN-only validation split (never TEST) instead
of the fixed 0.5 used by LR/RF; (b) cap or soften `pos_weight` (e.g.
`sqrt(n_neg/n_pos)` instead of the raw ratio) for the most-imbalanced folds;
(c) increase `TCN_MAX_EPOCHS`/reduce `lr` to see whether more stable
training avoids the early collapse; (d) inspect whether the small
per-fold TRAIN sets (as few as ~10-11 positive sequences for some CHB24
folds) are simply insufficient for this architecture regardless of
weighting. This should be resolved and re-evaluated on the SAME 57 folds
before either (i) treating TCN's H=30 AUC-PR win as real, or (ii)
proceeding to any paper-expansion item in Section 28.B.
