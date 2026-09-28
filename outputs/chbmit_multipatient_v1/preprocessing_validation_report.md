# CHB-MIT multipatient dataset v1 -- preprocessing validation report

- full run: False
- cases included: 24/24
- recordings processed: 43 (failures: 0)
- hours: 42.0; epochs: 5036
- channel set (18): FP1-F7, F7-T7, T7-P7, P7-O1, FP1-F3, F3-C3, C3-P3, P3-O1, FP2-F4, F4-C4, C4-P4, P4-O2, FP2-F8, F8-T8, T8-P8, P8-O2, FZ-CZ, CZ-PZ
- channel-wise dims: [5036, 252]; averaged dims: [5036, 14]
- backward validation passed: True (max rel feature diff 2.34e-15)
- QC: 18/18 passed
- artifact rejection: NOT IMPLEMENTED

## QC checks

- [PASS] no NaN/Inf in channel-wise features: 0 non-finite values
- [PASS] no NaN/Inf in channel-averaged features: 0 non-finite values
- [PASS] deterministic channel-wise columns: 252 cols = 18 channels x 14 features, channel-major order
- [PASS] consistent channel set for every recording: 43 recordings x 18 channels
- [PASS] epoch length 30 s: t_end - t_start
- [PASS] sampling frequency 256 Hz (7680 samples/epoch): all processed EDFs
- [PASS] no epoch crosses a recording boundary: t_end <= recording duration; epoch_idx contiguous 0..n-1 per recording
- [PASS] seizure-overlap metadata correct: independent interval-intersection recomputation
- [PASS] time-to-next-seizure metadata correct: independent brute-force recomputation, non-negative
- [PASS] every annotated seizure in a processed recording overlaps >= 1 epoch: 43/43; not covered: []
- [PASS] patient identity preserved: recording_id <-> patient_id <-> subject_id
- [PASS] recording identity preserved: recording_id <-> edf_name 1:1
- [PASS] no duplicate epochs: 5036 unique (recording_id, epoch_idx)
- [PASS] SHA256 integrity of every processed EDF: official SHA256SUMS.txt
- [PASS] duplicate labels: first-occurrence rule applied and non-identical cases documented: 11 non-identical duplicates documented in validation/duplicate_channel_labels.csv
- [PASS] all recordings accounted for / exclusions documented: {'patient_not_included': 640, 'processed': 43, 'excluded_before_processing': 3}
- [PASS] no processing failures: 0 failures
- [PASS] validated legacy outputs unchanged: 78 files sha256-compared

## Unresolved decisions

- seizure-free INTERICTAL -> LOSO fold association (Section 12 options)
- within-recording vs patient-timeline distances for labeling (Section 10)