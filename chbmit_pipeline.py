"""
Generalized CHB-MIT preprocessing + channel-wise qEEG feature pipeline.

ONE reusable implementation for every CHB-MIT case (replaces the per-patient
copy-paste pattern of EEG_CHB12_preprocessing.ipynb / EEG_CHB24_preprocessing.ipynb).
It is imported by EEG_chbmit_multipatient_preprocessing.ipynb, which is the
executed, reproducible record of the dataset build; the ``__main__`` CLI only
exists so the long download/extraction stage can run unattended -- it calls
exactly the same functions and writes exactly the same checkpoints.

Signal processing is intentionally IDENTICAL to the validated CHB24/CHB12
notebooks (see project_state.md Sections 18-20 and EEG_CHB24_preprocessing.ipynb
Step 5 helpers):

    EDF (MNE) -> keep named EEG channels -> MNE FIR band-pass 0.5-40 Hz
    -> non-overlapping 30 s epochs (leftover samples dropped, never padded)
    -> Welch PSD (nperseg = 2 s) -> the same 14 qEEG features

The only change is WHERE spatial aggregation happens: features are computed per
channel (final representation) and, from the very same epoch array, averaged
across channels with the legacy formulas (ablation/control representation).

Nothing in this module creates labels, folds, or models.
"""

from __future__ import annotations

import gc
import hashlib
import json
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Established preprocessing constants (unchanged from the validated pipeline)
# ---------------------------------------------------------------------------
FILTER_LOW_HZ = 0.5
FILTER_HIGH_HZ = 40.0
EPOCH_SEC = 30.0
EPOCH_OVERLAP = 0.0
EXPECTED_SFREQ = 256.0

FEATURES = [
    "std", "var", "rms", "delta", "theta", "alpha", "beta",
    "rel_delta", "rel_theta", "rel_alpha", "rel_beta",
    "theta_alpha_ratio", "delta_beta_ratio", "entropy",
]
BANDS = {"delta": (0.5, 4.0), "theta": (4.0, 8.0), "alpha": (8.0, 13.0), "beta": (13.0, 30.0)}
ENTROPY_BAND = (1.0, 40.0)
EPS = 1e-12

# The 23-channel montage used by the validated CHB12/CHB24 tables, in MNE
# runtime naming (MNE renames the duplicated "T8-P8" label to -0/-1).
LEGACY_23_CHANNELS = [
    "FP1-F7", "F7-T7", "T7-P7", "P7-O1", "FP1-F3", "F3-C3", "C3-P3", "P3-O1",
    "FP2-F4", "F4-C4", "C4-P4", "P4-O2", "FP2-F8", "F8-T8", "T8-P8-0", "P8-O2",
    "FZ-CZ", "CZ-PZ", "P7-T7", "T7-FT9", "FT9-FT10", "FT10-T8", "T8-P8-1",
]

# Standard 18-channel longitudinal bipolar ("double banana") 10-20 montage.
# These are the non-redundant derivations of the legacy montage that are not
# duplicates (T8-P8 appears twice, bitwise identical) or sign inversions
# (P7-T7 == -(T7-P7)). The three FT9/FT10 derivations are handled by the
# explicit availability rule in select_channel_set().
DOUBLE_BANANA_18 = [
    "FP1-F7", "F7-T7", "T7-P7", "P7-O1",
    "FP1-F3", "F3-C3", "C3-P3", "P3-O1",
    "FP2-F4", "F4-C4", "C4-P4", "P4-O2",
    "FP2-F8", "F8-T8", "T8-P8", "P8-O2",
    "FZ-CZ", "CZ-PZ",
]
FT_EXTENSION_3 = ["T7-FT9", "FT9-FT10", "FT10-T8"]

S3_BASE_URL = "https://physionet-open.s3.amazonaws.com/chbmit/1.0.0/"
PHYSIONET_BASE_URL = "https://physionet.org/files/chbmit/1.0.0/"

# Consecutive files closer than this are treated as one continuously observed
# block (only used for the descriptive observed_before/after_sec metadata).
CONTIGUITY_GAP_TOLERANCE_SEC = 60.0
EPOCH_CHUNK = 64  # epochs per feature-computation chunk (memory bound only; no effect on values)


# ---------------------------------------------------------------------------
# Naming conventions
# ---------------------------------------------------------------------------
def patient_subject_number(patient_id: str) -> int:
    m = re.fullmatch(r"chb(\d{2})", patient_id)
    if not m:
        raise ValueError(f"not a CHB-MIT case id: {patient_id}")
    return int(m.group(1))


def recording_id_from_edf(patient_id: str, edf_name: str) -> str:
    """chb12_06.edf -> chb_s12_r06 (existing convention); chb17a_03.edf -> chb_s17_ra03;
    chb02_16+.edf -> chb_s02_r16plus."""
    stem = Path(edf_name).stem
    m = re.fullmatch(r"(chb\d{2})([a-z]?)_(\d+)(\+?)", stem)
    if not m or m.group(1) != patient_id:
        raise ValueError(f"unexpected EDF name {edf_name} for {patient_id}")
    suffix = f"{m.group(2)}{m.group(3)}{'plus' if m.group(4) else ''}"
    return f"chb_s{patient_subject_number(patient_id):02d}_r{suffix}"


def normalize_channel_name(name: str) -> str:
    """FP1-F7 -> FP1_F7 (column-safe, deterministic)."""
    return re.sub(r"[^A-Z0-9]+", "_", name.upper()).strip("_")


def channelwise_columns(channels: list[str]) -> list[str]:
    """Channel-major, feature-minor order: for ch in channels: for f in FEATURES."""
    return [f"{f}__{normalize_channel_name(ch)}" for ch in channels for f in FEATURES]


# ---------------------------------------------------------------------------
# Summary parsing (generalizes the CHB24 parser + CHB12 montage-generation parser)
# ---------------------------------------------------------------------------
_SZ_START = re.compile(r"Seizure(?:\s+\d+)?\s+Start Time:\s*(\d+)\s*seconds")
_SZ_END = re.compile(r"Seizure(?:\s+\d+)?\s+End Time:\s*(\d+)\s*seconds")


def _hms_to_sec(s: str) -> float:
    h, m, sec = (int(x) for x in s.strip().split(":"))
    return h * 3600.0 + m * 60.0 + sec


def parse_summary(summary_path: Path) -> dict:
    """Parse chbXX-summary.txt.

    Returns {"sfreq": float|None, "montages": [list[str], ...],
             "files": [ {edf_name, montage_gen, declared_channels, start_clock,
                         end_clock, n_seizures, seizures: [(onset, offset), ...]} ]}
    in file order. Declared seizure counts are cross-checked against parsed
    onset/offset pairs (hard error on mismatch).
    """
    text = Path(summary_path).read_text()
    sf = re.search(r"Data Sampling Rate:\s*([\d.]+)\s*Hz", text)
    tokens = re.split(r"(?=File Name: |Channels changed:|Channels in EDF Files:)", text)
    montages: list[list[str]] = []
    files = []
    for tok in tokens:
        if tok.startswith("Channels in EDF Files:") or tok.startswith("Channels changed:"):
            montages.append(re.findall(r"Channel \d+:\s*(\S+)", tok))
            continue
        if not tok.startswith("File Name:"):
            continue
        fname = re.search(r"File Name:\s*(\S+)", tok).group(1)
        n = int(re.search(r"Number of Seizures in File:\s*(\d+)", tok).group(1))
        starts = [int(x) for x in _SZ_START.findall(tok)]
        ends = [int(x) for x in _SZ_END.findall(tok)]
        if len(starts) != n or len(ends) != n:
            raise ValueError(f"{fname}: declared {n} seizures, parsed {len(starts)}/{len(ends)}")
        if any(e <= s for s, e in zip(starts, ends)):
            raise ValueError(f"{fname}: seizure with end <= start")
        st = re.search(r"File Start Time:\s*([\d:]+)", tok)
        en = re.search(r"File End Time:\s*([\d:]+)", tok)
        files.append({
            "edf_name": fname,
            "montage_gen": len(montages) - 1,
            "declared_channels": list(montages[-1]) if montages else [],
            "start_clock": st.group(1) if st else None,
            "end_clock": en.group(1) if en else None,
            "n_seizures": n,
            "seizures": list(zip(starts, ends)),
        })
    return {"sfreq": float(sf.group(1)) if sf else None, "montages": montages, "files": files}


def build_timeline(files: list[dict]) -> pd.DataFrame:
    """Absolute (patient-timeline) start/end seconds for each summarized file.

    Clock times are wall-clock h:m:s that may exceed 24 h and wrap at midnight;
    a day is added whenever a start time would otherwise precede the previous
    file's end. Returns NaN for every file if any file lacks clock times.
    """
    rows = []
    if not files or any(f["start_clock"] is None or f["end_clock"] is None for f in files):
        for f in files:
            rows.append({"edf_name": f["edf_name"], "abs_start_sec": np.nan, "abs_end_sec": np.nan,
                         "summary_duration_sec": np.nan, "gap_before_sec": np.nan})
        return pd.DataFrame(rows)
    # Rule: files are listed chronologically; whole days are added to a clock
    # time until it is not earlier than the previous file's end (start) or the
    # file's own start (end). Gaps longer than 24 h cannot be detected from
    # clock times alone (documented limitation).
    prev_end = None
    for f in files:
        s = _hms_to_sec(f["start_clock"])
        if prev_end is not None:
            while s < prev_end - 1.0:
                s += 86400.0
        e = _hms_to_sec(f["end_clock"])
        while e < s:
            e += 86400.0
        rows.append({"edf_name": f["edf_name"], "abs_start_sec": s, "abs_end_sec": e,
                     "summary_duration_sec": e - s,
                     "gap_before_sec": np.nan if prev_end is None else s - prev_end})
        prev_end = e
    return pd.DataFrame(rows)


def load_corpus_index(meta_dir: Path) -> dict:
    """RECORDS, RECORDS-WITH-SEIZURES, SHA256SUMS, per-case summaries."""
    meta_dir = Path(meta_dir)
    records = [r.strip() for r in (meta_dir / "RECORDS").read_text().splitlines() if r.strip()]
    with_sz = {r.strip() for r in (meta_dir / "RECORDS-WITH-SEIZURES").read_text().splitlines() if r.strip()}
    sha = {}
    for line in (meta_dir / "SHA256SUMS.txt").read_text().splitlines():
        parts = line.split()
        if len(parts) == 2:
            sha[parts[1]] = parts[0]
    patients = sorted({r.split("/")[0] for r in records})
    summaries = {p: parse_summary(meta_dir / f"{p}-summary.txt") for p in patients}
    return {"records": records, "records_with_seizures": with_sz, "sha256": sha,
            "patients": patients, "summaries": summaries}


def patient_recording_table(index: dict, patient_id: str) -> pd.DataFrame:
    """One row per EDF in RECORDS for this case, merged with summary information."""
    summ = index["summaries"][patient_id]
    by_name = {f["edf_name"]: f for f in summ["files"]}
    tl = build_timeline(summ["files"]).set_index("edf_name")
    rows = []
    for rec in index["records"]:
        p, fname = rec.split("/")
        if p != patient_id:
            continue
        f = by_name.get(fname)
        in_rws = rec in index["records_with_seizures"]
        row = {
            "patient_id": patient_id,
            "edf_name": fname,
            "recording_id": recording_id_from_edf(patient_id, fname),
            "in_summary": f is not None,
            "in_records_with_seizures": in_rws,
            "sha256_expected": index["sha256"].get(rec),
            "montage_gen": f["montage_gen"] if f else np.nan,
            "declared_channels": json.dumps(f["declared_channels"] if f else
                                            (summ["montages"][0] if summ["montages"] else [])),
            "n_seizures": f["n_seizures"] if f else (np.nan if in_rws else 0),
            "seizures": json.dumps(f["seizures"] if f else []),
            "abs_start_sec": tl.loc[fname, "abs_start_sec"] if f else np.nan,
            "abs_end_sec": tl.loc[fname, "abs_end_sec"] if f else np.nan,
            "summary_duration_sec": tl.loc[fname, "summary_duration_sec"] if f else np.nan,
            "gap_before_sec": tl.loc[fname, "gap_before_sec"] if f else np.nan,
        }
        # Consistency: summary seizure count vs RECORDS-WITH-SEIZURES.
        if f is not None and (f["n_seizures"] > 0) != in_rws:
            row["annotation_conflict"] = True
        else:
            row["annotation_conflict"] = False
        rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Channel resolution (declared names at summary level, MNE runtime names later)
# ---------------------------------------------------------------------------
def declared_has_channels(declared: list[str], channels: list[str]) -> bool:
    have = Counter(declared)
    return all(have[c] >= 1 for c in channels)


def resolve_runtime_channels(runtime_names: list[str], channels: list[str]) -> dict:
    """Map each wanted bipolar derivation to the MNE runtime channel carrying it.

    MNE renames duplicated EDF labels with running numbers ("T8-P8" ->
    "T8-P8-0", "T8-P8-1"). A wanted name matches the exact runtime name, or
    its FIRST running-number duplicate (encounter order, the same channel the
    legacy pipeline listed first). Raises if a wanted channel is absent --
    missing channels are never invented or interpolated.
    """
    mapping = {}
    for ch in channels:
        if ch in runtime_names:
            mapping[ch] = ch
            continue
        dups = [n for n in runtime_names if re.fullmatch(re.escape(ch) + r"-\d+", n)]
        if not dups:
            raise KeyError(ch)
        mapping[ch] = dups[0]
    return mapping


# ---------------------------------------------------------------------------
# Download with integrity verification
# ---------------------------------------------------------------------------
def sha256_file(path: Path, chunk=1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def ensure_edf(raw_dir: Path, patient_id: str, edf_name: str, sha256_expected: str | None,
               retries: int = 3) -> tuple[Path, str]:
    """Return (path, status). Uses an existing file only if its SHA256 matches;
    otherwise downloads (AWS open-data mirror first, physionet.org fallback),
    verifies, and atomically renames. Status in {verified_existing, downloaded}."""
    dest = Path(raw_dir) / patient_id / edf_name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and sha256_expected and sha256_file(dest) == sha256_expected:
        return dest, "verified_existing"
    last_err = None
    for attempt in range(retries):
        for base in (S3_BASE_URL, PHYSIONET_BASE_URL):
            tmp = dest.with_suffix(dest.suffix + ".part")
            try:
                # URL-quote the name: chb02_16+.edf must be requested as chb02_16%2B.edf
                urllib.request.urlretrieve(f"{base}{patient_id}/{urllib.parse.quote(edf_name)}", tmp)
                digest = sha256_file(tmp)
                if sha256_expected and digest != sha256_expected:
                    raise IOError(f"SHA256 mismatch for {edf_name}: {digest}")
                shutil.move(str(tmp), str(dest))
                return dest, "downloaded"
            except (urllib.error.URLError, IOError, OSError) as e:
                last_err = e
                if tmp.exists():
                    tmp.unlink()
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"could not obtain {patient_id}/{edf_name}: {last_err}")


# ---------------------------------------------------------------------------
# Signal processing (identical to the validated helpers, vectorized)
# ---------------------------------------------------------------------------
def make_epochs(data: np.ndarray, sfreq: float, win_sec: float = EPOCH_SEC,
                overlap: float = EPOCH_OVERLAP) -> np.ndarray:
    """(channels, samples) -> (n_epochs, channels, win_samples); identical rule to the
    validated make_epochs(): zero overlap, leftover samples dropped. Operates on ONE
    recording, so an epoch can never span two recordings."""
    win = int(round(win_sec * sfreq))
    step = int(round(win * (1 - overlap)))
    if data.shape[1] < win:
        return np.empty((0, data.shape[0], win))
    starts = np.arange(0, data.shape[1] - win + 1, step)
    return np.stack([data[:, s:s + win] for s in starts], axis=0)


def compute_features(epochs: np.ndarray, sfreq: float) -> tuple[np.ndarray, np.ndarray]:
    """From ONE epoch array (E, C, N) return
        channelwise: (E, C, 14)  -- feature f of channel c, FEATURES order
        averaged:    (E, 14)     -- legacy channel-averaged definition
    Both come from the same Welch PSD. Legacy averaged formulas (verbatim
    semantics of the validated extract_features):
        std/var/rms over the flattened all-channel epoch;
        band powers = mean over channels of per-channel band power;
        relative powers / ratios from those averaged band powers;
        entropy = mean over channels of per-channel spectral entropy.
    """
    from scipy.signal import welch
    E, C, N = epochs.shape
    nperseg = min(N, int(2 * sfreq))
    freqs, psd = welch(epochs, fs=sfreq, nperseg=nperseg, axis=-1)  # (E, C, F)

    bp = {}
    for name, (lo, hi) in BANDS.items():
        m = (freqs >= lo) & (freqs <= hi)
        bp[name] = np.trapezoid(psd[..., m], freqs[m], axis=-1)  # (E, C)
    m = (freqs >= ENTROPY_BAND[0]) & (freqs <= ENTROPY_BAND[1])
    pb = np.maximum(psd[..., m], EPS)
    p = pb / pb.sum(axis=-1, keepdims=True)
    ent = -np.sum(p * np.log(p), axis=-1) / np.log(p.shape[-1])  # (E, C)

    std_c = np.std(epochs, axis=-1)
    var_c = np.var(epochs, axis=-1)
    rms_c = np.sqrt(np.mean(epochs ** 2, axis=-1))

    def derived(d, t, a, b):
        tot = d + t + a + b + EPS
        return d / tot, t / tot, a / tot, b / tot, t / (a + EPS), d / (b + EPS)

    rd, rt, ra, rb, tar, dbr = derived(bp["delta"], bp["theta"], bp["alpha"], bp["beta"])
    channelwise = np.stack([std_c, var_c, rms_c, bp["delta"], bp["theta"], bp["alpha"], bp["beta"],
                            rd, rt, ra, rb, tar, dbr, ent], axis=-1)  # (E, C, 14)

    flat = epochs.reshape(E, C * N)
    d_, t_, a_, b_ = (bp[k].mean(axis=1) for k in ("delta", "theta", "alpha", "beta"))
    ard, art, ara, arb, atar, adbr = derived(d_, t_, a_, b_)
    averaged = np.stack([np.std(flat, axis=1), np.var(flat, axis=1), np.sqrt(np.mean(flat ** 2, axis=1)),
                         d_, t_, a_, b_, ard, art, ara, arb, atar, adbr, ent.mean(axis=1)], axis=-1)
    return channelwise, averaged


@dataclass
class RecordingResult:
    recording_id: str
    n_epochs: int
    sfreq: float
    n_times: int
    duration_sec: float
    runtime_channels: list
    channel_map: dict
    duplicate_identical: dict = field(default_factory=dict)
    features: pd.DataFrame | None = None


def process_recording(edf_path: Path, recording_id: str, channels: list[str],
                      legacy_channels: list[str] | None = None,
                      expected_sfreq: float = EXPECTED_SFREQ) -> RecordingResult:
    """Load ONE EDF, keep the named channels, filter, epoch, extract features.

    Returns per-epoch features: channel-wise columns (channelwise_columns(channels)),
    averaged columns avg__<feature> over `channels`, and -- only when
    legacy_channels is given (backward-validation mode) -- legacy23__<feature>
    averaged over the legacy 23-channel runtime montage.
    """
    import mne
    raw = mne.io.read_raw_edf(edf_path, preload=False, verbose="ERROR")
    sfreq = float(raw.info["sfreq"])
    if not np.isclose(sfreq, expected_sfreq):
        raise ValueError(f"{recording_id}: sfreq {sfreq} != {expected_sfreq}")
    runtime = list(raw.ch_names)
    cmap = resolve_runtime_channels(runtime, channels)
    needed = list(dict.fromkeys(list(cmap.values()) + (legacy_channels or [])))
    missing_legacy = [c for c in (legacy_channels or []) if c not in runtime]
    if missing_legacy:
        raise KeyError(f"{recording_id}: legacy channels missing {missing_legacy}")

    # Duplicate-label QC: are MNE running-number duplicates of a used channel identical?
    dup_check = {}
    for want, rt in cmap.items():
        dups = [n for n in runtime if re.fullmatch(re.escape(want) + r"-\d+", n)]
        if len(dups) > 1:
            dup_check[want] = dups

    dup_extra = [n for dups in dup_check.values() for n in dups if n not in needed]
    raw.pick(needed + dup_extra)
    raw.load_data(verbose="ERROR")
    for want, dups in dup_check.items():
        d = raw.get_data(picks=dups)
        dup_check[want] = bool(all(np.array_equal(d[0], d[i]) for i in range(1, len(dups))))
    # Identical call to the validated preprocess_eeg(): MNE default FIR, zero-phase.
    raw.filter(l_freq=FILTER_LOW_HZ, h_freq=FILTER_HIGH_HZ, verbose="ERROR")
    data = raw.get_data(picks=needed)
    n_times = data.shape[1]
    if not np.isfinite(data).all():
        raise ValueError(f"{recording_id}: NaN/Inf after filtering")
    pos = {n: i for i, n in enumerate(needed)}
    del raw
    gc.collect()
    if n_times < int(round(EPOCH_SEC * sfreq)):
        raise ValueError(f"{recording_id}: shorter than one {EPOCH_SEC}s epoch")

    # Same epoch grid as make_epochs() (zero overlap, leftover dropped), built as a
    # zero-copy view; features are computed in chunks of epochs to bound memory.
    win = int(round(EPOCH_SEC * sfreq))
    E = n_times // win
    view = data[:, :E * win].reshape(data.shape[0], E, win).transpose(1, 0, 2)
    idx_main = [pos[cmap[c]] for c in channels]
    idx_leg = [pos[c] for c in legacy_channels] if legacy_channels else None
    cw_parts, av_parts, lav_parts = [], [], []
    for s in range(0, E, EPOCH_CHUNK):
        chunk = view[s:s + EPOCH_CHUNK]
        cw, av = compute_features(np.ascontiguousarray(chunk[:, idx_main, :]), sfreq)
        cw_parts.append(cw.reshape(cw.shape[0], -1))
        av_parts.append(av)
        if idx_leg is not None:
            lav_parts.append(compute_features(np.ascontiguousarray(chunk[:, idx_leg, :]), sfreq)[1])
    out = pd.DataFrame({"recording_id": recording_id, "epoch_idx": np.arange(E)})
    if E > 0:
        parts = [out,
                 pd.DataFrame(np.concatenate(cw_parts), columns=channelwise_columns(channels)),
                 pd.DataFrame(np.concatenate(av_parts), columns=[f"avg__{f}" for f in FEATURES])]
        if idx_leg is not None:
            parts.append(pd.DataFrame(np.concatenate(lav_parts), columns=[f"legacy23__{f}" for f in FEATURES]))
        out = pd.concat(parts, axis=1)
    del view, data
    gc.collect()
    return RecordingResult(recording_id, E, sfreq, n_times, n_times / sfreq, runtime, cmap,
                           dup_check, out)


# ---------------------------------------------------------------------------
# Checkpointing
# ---------------------------------------------------------------------------
def checkpoint_paths(ckpt_dir: Path, patient_id: str, recording_id: str) -> tuple[Path, Path]:
    d = Path(ckpt_dir) / patient_id
    return d / f"{recording_id}.parquet", d / f"{recording_id}.json"


def run_recording_to_checkpoint(raw_dir, ckpt_dir, patient_id, edf_name, recording_id, sha256_expected,
                                channels, legacy_channels=None, delete_edf_after=False) -> dict:
    """Idempotent: returns the provenance dict; skips work if a valid checkpoint exists
    for the same channel list / legacy flag."""
    pq, js = checkpoint_paths(ckpt_dir, patient_id, recording_id)
    want_cols = ["recording_id", "epoch_idx"] + channelwise_columns(channels) + [f"avg__{f}" for f in FEATURES]
    if legacy_channels:
        want_cols += [f"legacy23__{f}" for f in FEATURES]
    if pq.exists() and js.exists():
        prov = json.loads(js.read_text())
        if prov.get("channels") == channels and prov.get("legacy_channels") == legacy_channels:
            import pyarrow.parquet as papq
            cols = papq.read_schema(pq).names
            if cols == want_cols:
                prov["checkpoint_status"] = "reused"
                return prov
    pq.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    edf_path, dl_status = ensure_edf(raw_dir, patient_id, edf_name, sha256_expected)
    res = process_recording(edf_path, recording_id, channels, legacy_channels)
    res.features.to_parquet(pq, index=False)
    import mne, scipy
    prov = {
        "patient_id": patient_id, "edf_name": edf_name, "recording_id": recording_id,
        "sha256": sha256_expected, "download_status": dl_status,
        "sfreq": res.sfreq, "n_times": res.n_times, "duration_sec": res.duration_sec,
        "n_epochs": res.n_epochs, "leftover_sec": res.duration_sec - res.n_epochs * EPOCH_SEC,
        "channels": channels, "legacy_channels": legacy_channels,
        "channel_map": res.channel_map, "runtime_channels": res.runtime_channels,
        "duplicate_labels_identical": res.duplicate_identical,
        "filter_hz": [FILTER_LOW_HZ, FILTER_HIGH_HZ], "epoch_sec": EPOCH_SEC,
        "mne": mne.__version__, "numpy": np.__version__, "scipy": scipy.__version__,
        "seconds": round(time.time() - t0, 2), "checkpoint_status": "computed",
    }
    js.write_text(json.dumps(prov, indent=1))
    if delete_edf_after:
        edf_path.unlink()
    return prov


# ---------------------------------------------------------------------------
# Seizure / temporal metadata (epoch grid identical to add_temporal_metadata)
# ---------------------------------------------------------------------------
def epoch_metadata_for_recording(rec: dict, n_epochs: int, patient_seizures: pd.DataFrame,
                                 block_bounds: tuple[float, float] | None) -> pd.DataFrame:
    """Per-epoch metadata for one recording.

    Within-recording columns reproduce the validated definitions exactly:
      y_seizure (true interval intersection), seizure_id, next_seizure_id /
      next_seizure_start_sec / time_to_next_seizure_sec (first onset >= t_end in
      the SAME recording), previous_seizure_id / previous_seizure_end_sec /
      time_since_previous_seizure_sec (last end <= t_start in the SAME recording).
    Global columns use the patient timeline and ALL annotated seizures of the
    patient (including seizures in recordings that were not processed), NaN when
    the case has no clock times.
    """
    rid = rec["recording_id"]
    k = np.arange(n_epochs)
    t_start = k * EPOCH_SEC
    t_end = t_start + EPOCH_SEC
    df = pd.DataFrame({
        "patient_id": rec["patient_id"], "subject_id": patient_subject_number(rec["patient_id"]),
        "recording_id": rid, "edf_name": rec["edf_name"], "dataset": "chb",
        "epoch_idx": k, "t_start_sec": t_start, "t_center_sec": t_start + EPOCH_SEC / 2, "t_end_sec": t_end,
    })
    sz = patient_seizures[patient_seizures["recording_id"] == rid].sort_values("onset_sec")
    onsets = sz["onset_sec"].to_numpy(float)
    offsets = sz["offset_sec"].to_numpy(float)
    ids = sz["seizure_id"].tolist()

    y = np.zeros(n_epochs, dtype=int)
    sid = np.full(n_epochs, None, dtype=object)
    for on, off, i in zip(onsets, offsets, ids):
        ov = (t_start < off) & (t_end > on)
        y[ov] = 1
        sid[ov] = i  # later interval wins if two overlap one epoch (same as labeling notebook)
    df["y_seizure"] = y
    df["seizure_id"] = sid

    nx = np.searchsorted(onsets, t_end, side="left")
    has = nx < len(onsets)
    df["next_seizure_id"] = np.array([ids[i] if h else None for i, h in zip(nx, has)], dtype=object)
    df["next_seizure_start_sec"] = np.where(has, onsets[np.clip(nx, 0, max(len(onsets) - 1, 0))] if len(onsets) else np.nan, np.nan)
    df["time_to_next_seizure_sec"] = df["next_seizure_start_sec"] - t_end

    order = np.argsort(offsets, kind="stable")
    off_sorted = offsets[order]
    ids_sorted = [ids[i] for i in order]
    pv = np.searchsorted(off_sorted, t_start, side="right") - 1
    df["previous_seizure_id"] = np.array([ids_sorted[i] if i >= 0 else None for i in pv], dtype=object)
    df["previous_seizure_end_sec"] = np.where(pv >= 0, off_sorted[np.clip(pv, 0, None)] if len(off_sorted) else np.nan, np.nan)
    df["time_since_previous_seizure_sec"] = t_start - df["previous_seizure_end_sec"]

    # ---- global patient-timeline columns ----
    a0 = rec["abs_start_sec"]
    df["timeline_available"] = bool(np.isfinite(a0))
    df["abs_t_start_sec"] = a0 + t_start
    df["abs_t_end_sec"] = a0 + t_end
    ps = patient_seizures.dropna(subset=["abs_onset_sec"]).sort_values("abs_onset_sec")
    if np.isfinite(a0) and len(ps):
        g_on = ps["abs_onset_sec"].to_numpy(float)
        g_ids = ps["seizure_id"].tolist()
        gi = np.searchsorted(g_on, df["abs_t_end_sec"].to_numpy(), side="left")
        gh = gi < len(g_on)
        df["global_next_seizure_id"] = np.array([g_ids[i] if h else None for i, h in zip(gi, gh)], dtype=object)
        df["global_time_to_next_seizure_sec"] = np.where(gh, g_on[np.clip(gi, 0, len(g_on) - 1)], np.nan) - df["abs_t_end_sec"]
        pe = ps.sort_values("abs_offset_sec")
        g_off = pe["abs_offset_sec"].to_numpy(float)
        g_off_ids = pe["seizure_id"].tolist()
        gp = np.searchsorted(g_off, df["abs_t_start_sec"].to_numpy(), side="right") - 1
        df["global_previous_seizure_id"] = np.array([g_off_ids[i] if i >= 0 else None for i in gp], dtype=object)
        df["global_time_since_previous_seizure_sec"] = df["abs_t_start_sec"] - np.where(gp >= 0, g_off[np.clip(gp, 0, None)], np.nan)
    else:
        df["global_next_seizure_id"] = None
        df["global_time_to_next_seizure_sec"] = np.nan
        df["global_previous_seizure_id"] = None
        df["global_time_since_previous_seizure_sec"] = np.nan
    if block_bounds is not None and np.isfinite(a0):
        df["observed_before_sec"] = df["abs_t_start_sec"] - block_bounds[0]
        df["observed_after_sec"] = block_bounds[1] - df["abs_t_end_sec"]
    else:  # only the recording itself is known to be observed
        df["observed_before_sec"] = t_start
        df["observed_after_sec"] = rec["duration_sec"] - t_end
    df["recording_n_seizures"] = int(len(sz))
    return df


def patient_seizure_table(rec_table: pd.DataFrame) -> pd.DataFrame:
    """All annotated seizures of a case (every summarized recording, processed or not)."""
    rows = []
    for _, r in rec_table.iterrows():
        for k, (on, off) in enumerate(json.loads(r["seizures"])):
            rows.append({
                "patient_id": r["patient_id"], "recording_id": r["recording_id"], "edf_name": r["edf_name"],
                "seizure_id": f"{r['recording_id']}_sz{k}", "seizure_index_in_file": k,
                "onset_sec": float(on), "offset_sec": float(off), "duration_sec": float(off - on),
                "abs_onset_sec": r["abs_start_sec"] + on, "abs_offset_sec": r["abs_start_sec"] + off,
            })
    return pd.DataFrame(rows, columns=["patient_id", "recording_id", "edf_name", "seizure_id",
                                       "seizure_index_in_file", "onset_sec", "offset_sec", "duration_sec",
                                       "abs_onset_sec", "abs_offset_sec"])


def contiguous_blocks(rec_table: pd.DataFrame, tol: float = CONTIGUITY_GAP_TOLERANCE_SEC) -> dict:
    """recording_id -> (block_abs_start, block_abs_end) over ALL summarized files of the case
    (processed or not -- an unprocessed file is still observed EEG with annotations)."""
    t = rec_table.dropna(subset=["abs_start_sec"]).sort_values("abs_start_sec")
    out, cur, members = {}, None, []
    for _, r in t.iterrows():
        if cur is None or r["abs_start_sec"] - cur[1] > tol:
            for m in members:
                out[m] = tuple(cur)
            cur, members = [r["abs_start_sec"], r["abs_end_sec"]], []
        cur[1] = max(cur[1], r["abs_end_sec"])
        members.append(r["recording_id"])
    for m in members:
        out[m] = tuple(cur)
    return out


# ---------------------------------------------------------------------------
# Summary-level (pre-processing) eligibility estimate used ONLY for the
# patient-inclusion decision. Final eligibility is recomputed afterwards on the
# actual epochs with the validated make_binary_labels().
# ---------------------------------------------------------------------------
def summary_level_patient_stats(rec_table: pd.DataFrame, compatible: pd.Series,
                                preictal_min: float = 5.0, exclusion_min: float = 30.0) -> dict:
    """On the 30 s epoch grid implied by each compatible file's summary duration:
      eligible_within: seizures with >=1 PREICTAL epoch under the validated
                       (within-recording) postictal rule
      eligible_global: same, but the >=30 min postictal rule uses every annotated
                       seizure of the case on the patient timeline
      interictal_h_global: hours of epochs >=30 min from every annotated seizure
                       (both directions) on the patient timeline, compatible
                       files only; NaN if the case has no clock times
      interictal_h_within: same, within-recording distances only
    """
    H, X = preictal_min * 60.0, exclusion_min * 60.0
    sz = patient_seizure_table(rec_table)
    g_on = sz["abs_onset_sec"].to_numpy(float)
    g_off = sz["abs_offset_sec"].to_numpy(float)
    timeline = np.isfinite(g_on).all() and len(sz) > 0 and np.isfinite(rec_table["abs_start_sec"]).all()
    elig_w = elig_g = 0
    inter_w = inter_g = 0.0
    for (_, r), ok in zip(rec_table.iterrows(), compatible):
        if not ok:
            continue
        dur = r["summary_duration_sec"]
        seiz = json.loads(r["seizures"])
        if not np.isfinite(dur):
            # duration unknown before download (e.g. chb24): seizure files are known to span
            # >= their last offset; only the pre-onset part matters for eligibility.
            dur = max([off for _, off in seiz], default=0.0)
            count_inter = False
        else:
            count_inter = True
        n = int(dur // EPOCH_SEC)
        ts = np.arange(n) * EPOCH_SEC
        te = ts + EPOCH_SEC
        on = np.array([s for s, _ in seiz], float)
        off = np.array([e for _, e in seiz], float)
        overl = np.zeros(n, bool)
        for a, b in zip(on, off):
            overl |= (ts < b) & (te > a)
        # within-recording distances
        nxt = np.array([np.min(on[on >= t] - t) if np.any(on >= t) else np.inf for t in te])
        prv = np.array([np.min(t - off[off <= t]) if np.any(off <= t) else np.inf for t in ts])
        if timeline:
            a0 = r["abs_start_sec"]
            gn = np.array([np.min(g_on[g_on >= a0 + t] - (a0 + t)) if np.any(g_on >= a0 + t) else np.inf for t in te])
            gp = np.array([np.min(a0 + t - g_off[g_off <= a0 + t]) if np.any(g_off <= a0 + t) else np.inf for t in ts])
        for a in on:
            pre = (~overl) & (a - te > 0) & (a - te <= H) & np.isclose(nxt, a - te)
            elig_w += int(np.any(pre & (prv > X)))
            if timeline:
                elig_g += int(np.any(pre & (gp > X)))
        if count_inter:
            inter_w += np.sum((~overl) & (nxt > X) & (prv > X)) * EPOCH_SEC / 3600
            if timeline:
                inter_g += np.sum((~overl) & (gn > X) & (gp > X)) * EPOCH_SEC / 3600
    return {"eligible_within": elig_w, "eligible_global": elig_g if timeline else np.nan,
            "interictal_h_within": inter_w, "interictal_h_global": inter_g if timeline else np.nan,
            "timeline_available": bool(timeline)}


# ---------------------------------------------------------------------------
# Explicit, reproducible channel-set / recording / patient rules
# ---------------------------------------------------------------------------
MIN_ELIGIBLE_SEIZURES = 3      # LOSO: every fold trains on >= 2 other lead seizures
MIN_INTERICTAL_HOURS = 1.0     # sanity floor for FA/hour estimation
PATIENT_ORDER_FIRST = ["chb24", "chb12"]  # backward-validation patients processed first


def choose_channel_set(all_rec: pd.DataFrame) -> dict:
    """Rule: start from the non-redundant derivations of the validated legacy montage
    (18 standard longitudinal bipolar channels + T7-FT9, FT9-FT10, FT10-T8; the
    duplicate T8-P8 and the sign-inverted P7-T7 are redundant). Keep the 3 FT
    derivations only if EVERY recording that declares the 18 core channels also
    declares them; otherwise use the 18 core channels so no bipolar recording is
    lost for lack of an optional channel. Missing channels are never invented."""
    decl = all_rec["declared_channels"].apply(json.loads)
    has18 = decl.apply(lambda d: declared_has_channels(d, DOUBLE_BANANA_18))
    has21 = decl.apply(lambda d: declared_has_channels(d, DOUBLE_BANANA_18 + FT_EXTENSION_3))
    lost = all_rec[has18 & ~has21]
    use_ext = len(lost) == 0
    return {
        "channels": DOUBLE_BANANA_18 + (FT_EXTENSION_3 if use_ext else []),
        "ft_extension_used": use_ext,
        "files_with_core18": int(has18.sum()),
        "files_with_core18_but_not_ft3": int(len(lost)),
        "seizures_in_those_files": int(lost["n_seizures"].fillna(0).sum()),
        "patients_affected_by_ft3": sorted(lost["patient_id"].unique().tolist()),
        "files_without_core18": all_rec.loc[~has18, "edf_name"].tolist(),
    }


def build_selection(index: dict, legacy_recording_ids: set[str]) -> dict:
    """Recording compatibility + exclusion reasons, summary-level patient stats,
    inclusion decisions, and the processing plan (one row per EDF to process)."""
    all_rec = pd.concat([patient_recording_table(index, p) for p in index["patients"]], ignore_index=True)
    chan = choose_channel_set(all_rec)
    channels = chan["channels"]
    decl = all_rec["declared_channels"].apply(json.loads)
    all_rec["montage_compatible_declared"] = decl.apply(lambda d: declared_has_channels(d, channels))

    reasons = []
    for _, r in all_rec.iterrows():
        rs = []
        if not r["montage_compatible_declared"]:
            miss = [c for c in channels if c not in json.loads(r["declared_channels"])]
            rs.append(f"montage_incompatible: declared montage lacks {len(miss)} of {len(channels)} "
                      f"required channels (e.g. {miss[:3]}); non-bipolar/different reference scheme")
        if r["in_records_with_seizures"] and not r["in_summary"]:
            rs.append("seizure_times_unavailable: listed with seizures but absent from summary")
        if not r["sha256_expected"]:
            rs.append("no_official_checksum")
        reasons.append("; ".join(rs))
    all_rec["exclusion_reason_pre"] = reasons

    pat_rows = []
    for p, g in all_rec.groupby("patient_id", sort=True):
        ok = g["exclusion_reason_pre"] == ""
        st = summary_level_patient_stats(g, ok)
        elig = st["eligible_global"] if st["timeline_available"] else st["eligible_within"]
        inter = st["interictal_h_global"] if st["timeline_available"] else np.nan
        reasons_p = []
        if int(g["n_seizures"].fillna(0).sum()) == 0:
            reasons_p.append("no seizure annotations")
        if elig < MIN_ELIGIBLE_SEIZURES:
            reasons_p.append(f"eligible lead seizures {elig} < {MIN_ELIGIBLE_SEIZURES}")
        if np.isfinite(inter) and inter < MIN_INTERICTAL_HOURS:
            reasons_p.append(f"candidate interictal {inter:.1f} h < {MIN_INTERICTAL_HOURS} h")
        pat_rows.append({
            "patient_id": p, "n_recordings": len(g), "n_recordings_compatible": int(ok.sum()),
            "summary_hours_total": g["summary_duration_sec"].sum() / 3600,
            "summary_hours_compatible": g.loc[ok, "summary_duration_sec"].sum() / 3600,
            "n_seizures_annotated": int(g["n_seizures"].fillna(0).sum()),
            "n_seizures_in_compatible": int(g.loc[ok, "n_seizures"].fillna(0).sum()),
            "eligible_seizures_within_est": st["eligible_within"],
            "eligible_seizures_global_est": st["eligible_global"],
            "interictal_h_within_est": st["interictal_h_within"],
            "interictal_h_global_est": st["interictal_h_global"],
            "timeline_available": st["timeline_available"],
            "included": len(reasons_p) == 0,
            "inclusion_note": ("interictal hours unknown before download (no clock times); "
                               "re-checked after processing" if not st["timeline_available"] else ""),
            "exclusion_reason": "; ".join(reasons_p),
        })
    patients = pd.DataFrame(pat_rows)
    inc = patients.loc[patients["included"], "patient_id"].tolist()
    order = [p for p in PATIENT_ORDER_FIRST if p in inc] + [p for p in inc if p not in PATIENT_ORDER_FIRST]
    plan_rows = []
    for p in order:
        g = all_rec[(all_rec["patient_id"] == p) & (all_rec["exclusion_reason_pre"] == "")]
        for _, r in g.iterrows():
            plan_rows.append({
                "patient_id": p, "edf_name": r["edf_name"], "recording_id": r["recording_id"],
                "sha256_expected": r["sha256_expected"], "channels": json.dumps(channels),
                "legacy_channels": json.dumps(LEGACY_23_CHANNELS) if r["recording_id"] in legacy_recording_ids else "",
            })
    return {"recordings": all_rec, "channel_rule": chan, "channels": channels,
            "patients": patients, "plan": pd.DataFrame(plan_rows)}


def wait_for_file(path: Path, wait_sec: float, poll: float = 10.0) -> bool:
    waited = 0.0
    while not Path(path).exists() and waited < wait_sec:
        time.sleep(poll)
        waited += poll
    return Path(path).exists()


# ---------------------------------------------------------------------------
# CLI (long unattended extraction; same functions as the notebook)
# ---------------------------------------------------------------------------
def _cli():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("plan_csv", help="processing plan CSV written by the notebook (one row per EDF)")
    ap.add_argument("--raw-dir", required=True)
    ap.add_argument("--ckpt-dir", required=True)
    ap.add_argument("--delete-edf-after", action="store_true")
    ap.add_argument("--wait-sec", type=float, default=0.0,
                    help="wait up to this long for an external downloader to deliver a missing EDF")
    a = ap.parse_args()
    plan = pd.read_csv(a.plan_csv)
    for i, r in plan.iterrows():
        wait_for_file(Path(a.raw_dir) / r["patient_id"] / r["edf_name"], a.wait_sec)
        channels = json.loads(r["channels"])
        legacy = json.loads(r["legacy_channels"]) if isinstance(r["legacy_channels"], str) and r["legacy_channels"] else None
        try:
            prov = run_recording_to_checkpoint(a.raw_dir, a.ckpt_dir, r["patient_id"], r["edf_name"],
                                               r["recording_id"], r["sha256_expected"], channels, legacy,
                                               a.delete_edf_after)
            print(f"[{i+1}/{len(plan)}] {r['recording_id']}: {prov['checkpoint_status']} "
                  f"epochs={prov['n_epochs']} t={prov.get('seconds')}", flush=True)
        except Exception as e:  # recorded, never silently skipped
            print(f"[{i+1}/{len(plan)}] {r['recording_id']}: FAILED {type(e).__name__}: {e}", flush=True)


if __name__ == "__main__":
    _cli()
