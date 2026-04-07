"""
harmonize_data.py
=================
Harmonizes 5 REDCap study datasets into a single analytic dataset
for POP recurrence prediction modeling.

Inputs:  data/*_DATA_LABELS_*.csv  (REDCap label exports — column headers are
         full human-readable question text, NOT short variable names)
Output:  data/harmonized_data.csv

Recurrence outcome (composite) — applied at any follow-up visit with POP-Q data:
  1. POP-Q Stage >= 2
  2. Any POP-Q point (Aa, Ba, C, Ap, Bp) >= 0
  3. Bothersome vaginal bulge on PFDI-20 Q3

See procedure/claude/data_harmonizing_decisions.md for full methodology.
"""

import os
import re
import logging
import warnings
from datetime import datetime

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FILE PATHS
# ---------------------------------------------------------------------------

STUDY_FILES = {
    "ALTIS": "data/ALTIS_DATA_LABELS_2025-10-02_1054.csv",
    "BEST":  "data/BEST_DATA_LABELS_2025-10-02_1045.csv",
    "EPACT": "data/EPACT_DATA_LABELS_2025-10-02_1057.csv",
    "SASS":  "data/SASS_DATA_LABELS_2025-10-02_1051.csv",
    "ELOVE": "data/ELOVE_DATA_LABELS_2025-10-02_1048.csv",
}
OUTPUT_FILE = "data/harmonized_data.csv"

# ---------------------------------------------------------------------------
# STUDY CONFIGURATION
# ---------------------------------------------------------------------------

BASELINE_EVENTS = {
    "ALTIS": "Baseline",
    "BEST":  "Baseline",
    "EPACT": "Baseline",
    "SASS":  "Baseline",
    "ELOVE": "Baseline Visit",
}

# Surgery type fixed by study design; ALTIS is derived per-patient
SURGERY_TYPE_FIXED = {
    "BEST":  "sacrocolpopexy",
    "EPACT": "sacrocolpopexy",
    "SASS":  "sacrocolpopexy",
    "ELOVE": "none",
}

# BEST uses "Record ID" as its study ID column; all others use "Study ID"
ID_COLS = {
    "BEST": "Record ID",
}


# ---------------------------------------------------------------------------
# LOW-LEVEL HELPERS
# ---------------------------------------------------------------------------

def load_study(path: str) -> pd.DataFrame:
    """Load a study CSV (BOM-safe, all columns as strings)."""
    return pd.read_csv(path, encoding="utf-8-sig", low_memory=False, dtype=str)


def to_float(val) -> float:
    """Convert a value to float, returning NaN on failure."""
    if val is None:
        return np.nan
    if isinstance(val, float) and np.isnan(val):
        return np.nan
    s = str(val).strip()
    if s in ("", "NA", "N/A", "na", "nan", "NaN", "n/a"):
        return np.nan
    try:
        return float(s)
    except ValueError:
        return np.nan


def is_yes(val) -> bool:
    """Return True if value indicates checked / yes / positive."""
    if val is None:
        return False
    if isinstance(val, float) and np.isnan(val):
        return False
    s = str(val).strip().lower()
    return s in ("yes", "checked", "1", "true", "y")


# ---------------------------------------------------------------------------
# COLUMN SEARCH HELPERS
# ---------------------------------------------------------------------------

def find_value(row: pd.Series, *patterns: str, case_sensitive: bool = False):
    """
    Return the first non-empty string value from columns whose names contain
    any of the given substrings.  Returns None if nothing matches.
    """
    for col in row.index:
        col_cmp = col if case_sensitive else col.lower()
        for pat in patterns:
            pat_cmp = pat if case_sensitive else pat.lower()
            if pat_cmp in col_cmp:
                val = row[col]
                if pd.notna(val) and str(val).strip():
                    return str(val).strip()
    return None


def find_numeric(row: pd.Series, *patterns: str, case_sensitive: bool = False) -> float:
    """
    Return the first non-NaN numeric value from columns whose names contain
    any of the given substrings.  Skips columns whose values don't parse as float.
    """
    for col in row.index:
        col_cmp = col if case_sensitive else col.lower()
        for pat in patterns:
            pat_cmp = pat if case_sensitive else pat.lower()
            if pat_cmp in col_cmp:
                f = to_float(row[col])
                if not np.isnan(f):
                    return f
    return np.nan


# ---------------------------------------------------------------------------
# POP-Q HELPERS
# ---------------------------------------------------------------------------

# Pre-compile patterns for each POP-Q point.
# Matches: 'Aa', 'Aa.1', 'Aa.2', 'Aa:' — the variants used across timepoints.
_POPQ_PATTERNS = {
    pt: re.compile(rf"^{re.escape(pt)}(\.\d+|:)?$")
    for pt in ["Aa", "Ba", "C", "Ap", "Bp", "gh", "pb", "tvl", "D"]
}


def get_popq_point(row: pd.Series, point: str) -> float:
    """
    Return the numeric POP-Q measurement for `point` from an event row.
    Handles baseline ('Aa'), 6-week ('Aa.1'), 1-year ('Aa:'), etc.
    """
    pat = _POPQ_PATTERNS[point]
    for col in row.index:
        if pat.match(col):
            val = row[col]
            if pd.isna(val):   # must check before str() — str(NaN)='nan' passes empty check
                continue
            s = str(val).strip()
            if s.lower() not in ("na", "n/a", "", "nan"):
                try:
                    return float(s)
                except ValueError:
                    pass
    return np.nan


def get_popq_stage(row: pd.Series) -> float:
    """
    Return numeric POP-Q stage from an event row.
    Handles:
      - ALTIS/SASS: 'Stage:  (long desc)' = '4.0', 'Stage:' = '0.0', 'Stage:.1'
      - EPACT:      '11. POP-Q stage:'  or  '22. POP-Q stage:' = 'Stage 2'
      - BEST:       'Stage:  (Minimum...)' or '4. POP-Q stage:' = 'Stage 2'
    """
    for col in row.index:
        cl = col.strip()
        if cl.startswith("Stage:") or "pop-q stage" in cl.lower() or "popq stage" in cl.lower():
            val = row[col]
            if pd.notna(val) and str(val).strip():
                s = str(val).strip()
                try:
                    return float(s)
                except ValueError:
                    m = re.search(r"(\d+)", s)
                    if m:
                        return float(m.group(1))
    return np.nan


def get_popq_from_row(row: pd.Series) -> dict:
    """Extract all POP-Q measurements and stage from an event row."""
    result = {}
    for pt in ["Aa", "Ba", "C", "Ap", "Bp", "gh", "pb", "tvl", "D"]:
        result[pt.lower()] = get_popq_point(row, pt)
    result["stage"] = get_popq_stage(row)
    return result


# ---------------------------------------------------------------------------
# PFDI-20 Q3 BULGE BOTHER
# ---------------------------------------------------------------------------

def get_bulge_bother(row: pd.Series):
    """
    Find and parse PFDI-20 Q3 (vaginal bulge) bother response.
    Returns: 1 (bothersome), 0 (not bothersome), or np.nan.

    Response formats across studies:
      - ALTIS/EPACT direct: 'No' / 'Not at all' / 'Somewhat' / 'Moderately' / 'Quite a bit'
      - SASS combined:       'No' / 'Yes, and it somewhat/moderately bothers me'
      - EPACT baseline:      'Yes' / 'No'  (no bother level — returns NaN)
      - Two-part (EPACT early follow-up): yes/no + companion bother column
    """
    bulge_col = None
    bother_companion = None

    for col in row.index:
        cl = col.lower()
        # Skip eligibility / AE / other non-PFDI bulge references
        if ("vaginal bulge symptoms" in cl or "eligib" in cl or
                "palpable" in cl or "vaginal area with your fingers" in cl):
            continue
        if ("bulge" in cl or "buldge" in cl or "falling out" in cl) and "pfdi" not in cl:
            val = row[col]
            if pd.notna(val) and str(val).strip():
                bulge_col = col
                break

    if bulge_col is None:
        return np.nan

    # Also search for a companion "how much does this bother you" question
    for col in row.index:
        if "how much does this bother" in col.lower():
            val = row[col]
            if pd.notna(val) and str(val).strip():
                bother_companion = col
                break

    val = str(row[bulge_col]).strip().lower()

    # Direct bother-scale responses
    if val in ("no", "not at all", "not at all."):
        return 0
    if any(x in val for x in ("somewhat", "moderately", "quite a bit", "yes, and")):
        return 1

    # Pure yes (EPACT baseline): look for companion bother column
    if val == "yes":
        if bother_companion is not None:
            bval = str(row[bother_companion]).strip().lower()
            if bval in ("not at all",):
                return 0
            if any(x in bval for x in ("somewhat", "moderately", "quite a bit")):
                return 1
        return np.nan  # Can't determine bother level without companion

    return np.nan


# ---------------------------------------------------------------------------
# DEMOGRAPHIC PARSERS
# ---------------------------------------------------------------------------

def parse_hormonal_status(val) -> float:
    """
    Parse hormonal status text to 0–3 scale:
      0 = Pre/peri-menopausal
      1 = Postmenopausal, no HRT
      2 = Postmenopausal, vaginal estrogen
      3 = Postmenopausal, oral/systemic HRT
    """
    if val is None:
        return np.nan
    v = str(val).lower().strip()
    v = re.sub(r"^\d+\.\s*", "", v)  # strip leading '1. ' prefix (ELOVE)
    if "pre" in v or "peri" in v:
        return 0.0
    if "vaginal" in v or "local" in v:
        return 2.0
    if "oral" in v or "systemic" in v:
        return 3.0
    if "no hormone" in v or "no hrt" in v or "no hor" in v:
        return 1.0
    if "postmeno" in v or "post-meno" in v:
        return 1.0  # generic postmenopausal, default to no HRT
    return np.nan


def parse_smoking(val) -> float:
    """Parse smoking status: 0 = never, 1 = ever (previous or current), NaN = unknown."""
    if val is None:
        return np.nan
    v = str(val).lower().strip()
    v = re.sub(r"^\d+\.\s*", "", v)
    if "never" in v:
        return 0.0
    if any(x in v for x in ("previous", "former", "ex-", "current")):
        return 1.0
    return np.nan


def parse_age_from_dob(dob_str, ref_date_str) -> float:
    """Calculate age in years from DOB and a reference date (both as strings)."""
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            dob = datetime.strptime(str(dob_str).strip(), fmt)
            ref = datetime.strptime(str(ref_date_str).strip(), fmt)
            return round((ref - dob).days / 365.25, 1)
        except (ValueError, TypeError):
            continue
    return np.nan


def parse_ethnicity(row: pd.Series) -> float:
    """Parse ethnicity to 1 (Hispanic) / 0 (Not Hispanic) / NaN."""
    val = find_value(row, "ethnicity")
    if val is None:
        return np.nan
    v = val.lower()
    if any(x in v for x in ("not hispanic", "neither hispanic", "no hispanic")):
        return 0.0
    if "hispanic" in v:
        return 1.0
    return np.nan


def parse_race_checkboxes(row: pd.Series, study: str):
    """
    Parse race indicators.
    ELOVE uses a single 'Race' column with a text value.
    All others use checkbox columns with '(choice=...)' patterns.
    Returns (race_white, race_black, race_other) as 0/1 ints.
    """
    race_white = race_black = race_other = 0

    if study == "ELOVE":
        race_val = find_value(row, "race")
        if race_val:
            rv = race_val.lower()
            if "white" in rv or "caucasian" in rv:
                race_white = 1
            elif "black" in rv or "african" in rv:
                race_black = 1
            elif rv not in ("", "unknown"):
                race_other = 1
    else:
        for col in row.index:
            cl = col.lower()
            if "choice=" not in cl and "(choice" not in cl:
                continue
            if not is_yes(row[col]):
                continue
            if "white" in cl or "caucasian" in cl:
                race_white = 1
            elif "black" in cl or "african" in cl:
                race_black = 1
            elif any(x in cl for x in ("other", "native", "pacific", "alaska", "american indian", "asian")):
                race_other = 1

    return race_white, race_black, race_other


def derive_race_category(race_white, race_black, race_other, ethnicity_hispanic) -> str:
    """Priority: Hispanic > White > Black > Other."""
    if ethnicity_hispanic == 1:
        return "Hispanic"
    if race_white == 1:
        return "White"
    if race_black == 1:
        return "Black"
    if race_other == 1:
        return "Other"
    return "Unknown"


# ---------------------------------------------------------------------------
# COMORBIDITY EXTRACTION
# ---------------------------------------------------------------------------

def parse_comorbidities(row: pd.Series):
    """
    Extract diabetes, cardiovascular disease, and pulmonary disease.

    ALTIS/SASS/BEST: use Charlson score component columns (numeric, >0 = positive)
    EPACT:           use '16x. ...' YES/No columns
    Both fallbacks applied in order.

    Returns (diabetes, cvd, pulmonary) each as 0.0 / 1.0 / NaN.
    """
    # --- Diabetes ---
    diab = np.nan
    d1 = find_numeric(row, "diabetes, 1 point")
    d2 = find_numeric(row, "diabetes with end organ")
    if not (np.isnan(d1) and np.isnan(d2)):
        diab = 1.0 if (d1 or 0) > 0 or (d2 or 0) > 0 else 0.0
    else:
        v = find_value(row, "16j. diabetes")
        if v:
            diab = 0.0 if "no" == v.strip().lower() else 1.0
        else:
            v2 = find_value(row, "13. diabetes")
            if v2:
                diab = 1.0 if v2.strip().upper() == "YES" else 0.0

    # --- Cardiovascular disease ---
    cvd = np.nan
    charlson_cvd = [
        find_numeric(row, "myocardial infarction, 1 point"),
        find_numeric(row, "congestive heart failure, 1 point"),
        find_numeric(row, "peripheral vascular disease, 1 point"),
        find_numeric(row, "cerebrovascular disease, 1 point"),
    ]
    if any(not np.isnan(v) for v in charlson_cvd):
        cvd = 1.0 if any((v or 0) > 0 for v in charlson_cvd if not np.isnan(v)) else 0.0
    else:
        epact_cvd = [
            find_value(row, "16a. myocardial"),
            find_value(row, "16b. congestive"),
            find_value(row, "16c. peripheral vasc"),
            find_value(row, "16d. cerebro"),
        ]
        valid = [v for v in epact_cvd if v is not None]
        if valid:
            cvd = 1.0 if any(v.lower() != "no" for v in valid) else 0.0

    # --- Pulmonary (COPD) ---
    pulm = np.nan
    p1 = find_numeric(row, "chronic pulmonary disease, 1 point")
    if not np.isnan(p1):
        pulm = 1.0 if p1 > 0 else 0.0
    else:
        v = find_value(row, "16f. chronic obstruc", "chronic obstructive pulmonary",
                       "7. chronic obstrucive pulmonary")
        if v:
            pulm = 0.0 if v.strip().lower() == "no" else 1.0

    return diab, cvd, pulm


# ---------------------------------------------------------------------------
# DEMOGRAPHICS EXTRACTION
# ---------------------------------------------------------------------------

def extract_demographics(row: pd.Series, study: str) -> dict:
    """Extract and harmonize demographics from a baseline event row."""

    # --- Age ---
    if study == "ELOVE":
        dob = find_value(row, "date of birth")
        ref = find_value(row, "date subject signed consent", "date icf obtained",
                         "baseline visit date")
        age = parse_age_from_dob(dob, ref) if dob and ref else np.nan
    else:
        # Search in priority: specific patterns first, then fall back
        age = find_numeric(row, "age in years:", "age:", "1. age:")
        if np.isnan(age):
            age = find_numeric(row, "age")  # BEST has plain 'Age'

    # --- Height / Weight / BMI ---
    height = find_numeric(row, "height (cm)", "height:")
    weight = find_numeric(row, "weight (kg)", "weight :")
    bmi = (weight / ((height / 100) ** 2)
           if not np.isnan(height) and not np.isnan(weight) and height > 0
           else np.nan)

    # --- Obstetric history ---
    parity  = find_numeric(row, "parity")
    vag_del = find_numeric(row, "vaginal deliveries", "3. vaginal deliveries")
    csect   = find_numeric(row, "caesarean section", "4. caesarean sections")

    # --- Hormonal status ---
    horm_val = find_value(row, "hormonal status")
    hormonal_status = parse_hormonal_status(horm_val)

    # --- Smoking ---
    # Use specific patterns first to avoid matching unrelated columns
    smoke_val = None
    for pat in ("smoking/tobacco usage", "9. smoking", "smoking:"):
        smoke_val = find_value(row, pat)
        if smoke_val:
            break
    if smoke_val is None:
        smoke_val = find_value(row, "smoking")
    smoking_ever = parse_smoking(smoke_val)

    # --- Race / Ethnicity ---
    race_white, race_black, race_other = parse_race_checkboxes(row, study)
    ethnicity_hispanic = parse_ethnicity(row)
    race_hispanic = 1 if ethnicity_hispanic == 1 else 0
    race_category = derive_race_category(race_white, race_black, race_other,
                                          ethnicity_hispanic)

    # --- Comorbidities ---
    diabetes, cvd, pulm = parse_comorbidities(row)

    return {
        "age":                age,
        "height_cm":          height,
        "weight_kg":          weight,
        "bmi":                bmi,
        "parity":             parity,
        "vaginal_deliveries": vag_del,
        "csections":          csect,
        "hormonal_status":    hormonal_status,
        "smoking_ever":       smoking_ever,
        "ethnicity_hispanic": ethnicity_hispanic,
        "race_white":         race_white,
        "race_black":         race_black,
        "race_hispanic":      race_hispanic,
        "race_other":         race_other,
        "race_category":      race_category,
        "diabetes":           diabetes,
        "cardiovascular_disease": cvd,
        "pulmonary_disease":  pulm,
    }


# ---------------------------------------------------------------------------
# BASELINE POP-Q
# ---------------------------------------------------------------------------

def extract_baseline_popq(row: pd.Series) -> dict:
    """Extract baseline POP-Q measurements and symptom from a baseline event row."""
    popq = get_popq_from_row(row)
    bulge = get_bulge_bother(row)
    return {
        "bas_aa":               popq["aa"],
        "bas_ba":               popq["ba"],
        "bas_c":                popq["c"],
        "bas_gh":               popq["gh"],
        "bas_pb":               popq["pb"],
        "bas_tvl":              popq["tvl"],
        "bas_ap":               popq["ap"],
        "bas_bp":               popq["bp"],
        "bas_d":                popq["d"],
        "bas_stage":            popq["stage"],
        "bas_bulge_bothersome": bulge,
    }


# ---------------------------------------------------------------------------
# SURGERY TYPE (ALTIS)
# ---------------------------------------------------------------------------

def derive_surgery_type_altis(surgery_rows: pd.DataFrame) -> str:
    """
    Derive ALTIS surgery type from surgical procedure checkbox columns.
    Colpocleisis takes priority; otherwise native tissue repair.
    """
    for _, row in surgery_rows.iterrows():
        for col in row.index:
            if "colpoclesis" in col.lower() or "colpocleisis" in col.lower():
                if is_yes(row[col]):
                    return "colpocleisis"
    return "native_tissue"


# ---------------------------------------------------------------------------
# RECURRENCE EVALUATION
# ---------------------------------------------------------------------------

def check_recurrence_on_row(row: pd.Series):
    """
    Evaluate composite recurrence criteria on a single follow-up event row.
    Returns (recurred: bool, has_outcome_data: bool).
    """
    popq = get_popq_from_row(row)
    bother = get_bulge_bother(row)

    has_popq = any(not np.isnan(popq[pt]) for pt in ["aa", "ba", "c", "ap", "bp", "stage"])
    has_data = has_popq or (bother is not None and not np.isnan(bother))

    # Criterion 1: Stage >= 2
    if not np.isnan(popq["stage"]) and popq["stage"] >= 2:
        return True, True

    # Criterion 2: Any point >= 0
    for pt in ["aa", "ba", "c", "ap", "bp"]:
        if not np.isnan(popq[pt]) and popq[pt] >= 0:
            return True, True

    # Criterion 3: Bothersome bulge
    if bother == 1:
        return True, has_data

    return False, has_data


def _is_six_week_event(event_name: str) -> bool:
    """Return True if the event name refers to a 6-week follow-up visit."""
    e = event_name.lower().strip()
    return "6 week" in e or "6wk" in e or e.startswith("w6 ") or e == "6wk visit"


def evaluate_patient_recurrence(patient_rows: pd.DataFrame, baseline_event: str) -> dict:
    """
    Scan all non-baseline event rows for composite recurrence.

    6-week visit handling:
      - If the patient has any later (non-6wk) follow-up with outcome data, the 6-week
        visit is excluded from recurrence assessment (transient post-op finding).
      - If 6-week is the patient's only follow-up with outcome data, it is retained
        as the last known observation.

    Returns dict: recurred, n_followup_visits_with_popq, first_recurrence_event.
    """
    fu_rows = patient_rows[
        patient_rows["Event Name"].str.strip() != baseline_event
    ]

    # Determine whether any non-6wk follow-up visits have outcome data
    non_six_wk_has_data = any(
        check_recurrence_on_row(row)[1]
        for _, row in fu_rows.iterrows()
        if not _is_six_week_event(str(row["Event Name"]))
    )

    recurred = False
    n_visits = 0
    first_event = np.nan

    for _, row in fu_rows.iterrows():
        is_6wk = _is_six_week_event(str(row["Event Name"]))
        # Skip 6-week visit if later outcome data exists
        if is_6wk and non_six_wk_has_data:
            continue

        rec, has_data = check_recurrence_on_row(row)
        if has_data:
            n_visits += 1
        if rec and not recurred:
            recurred = True
            first_event = row["Event Name"]

    return {
        "recurred":                    recurred,
        "n_followup_visits_with_popq": n_visits,
        "first_recurrence_event":      first_event,
    }


# ---------------------------------------------------------------------------
# PER-STUDY HARMONIZATION
# ---------------------------------------------------------------------------

def harmonize_study(study: str, path: str) -> pd.DataFrame:
    """Load and harmonize one study. Returns one-row-per-patient DataFrame."""
    log.info(f"Loading {study} from {path}")
    df = load_study(path)

    if "Event Name" not in df.columns:
        log.warning(f"{study}: no 'Event Name' column; skipping")
        return pd.DataFrame()

    # Standardize the patient ID column
    id_col = ID_COLS.get(study, "Study ID")
    if id_col not in df.columns:
        id_col = df.columns[0]
    df = df.rename(columns={id_col: "study_id"})

    baseline_event = BASELINE_EVENTS[study]
    fixed_surgery  = SURGERY_TYPE_FIXED.get(study)

    unique_ids = df["study_id"].dropna().unique()
    log.info(f"  {study}: {len(unique_ids)} unique patient IDs")

    records = []
    for pid in unique_ids:
        patient_rows = df[df["study_id"] == pid].copy()
        baseline_rows = patient_rows[
            patient_rows["Event Name"].str.strip() == baseline_event
        ]
        if baseline_rows.empty:
            log.debug(f"  {study}/{pid}: no baseline row, skipping")
            continue

        bas_row = baseline_rows.iloc[0]

        demo   = extract_demographics(bas_row, study)
        popq   = extract_baseline_popq(bas_row)
        rec    = evaluate_patient_recurrence(patient_rows, baseline_event)

        if fixed_surgery:
            surgery_type = fixed_surgery
        else:
            # ALTIS: infer from surgery event row
            surg_rows = patient_rows[
                patient_rows["Event Name"].str.strip().str.lower().str.rstrip()
                .isin(["surgery", "day of surgery", "surgical procedure"])
            ]
            surgery_type = derive_surgery_type_altis(surg_rows)

        record = {
            "patient_id":   f"{study}_{pid}",
            "study":        study,
            "surgery_type": surgery_type,
            **demo,
            **popq,
            **rec,
        }
        records.append(record)

    result = pd.DataFrame(records)
    log.info(f"  {study}: {len(result)} patients harmonized")
    return result


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    all_dfs = []
    for study, path in STUDY_FILES.items():
        if not os.path.exists(path):
            log.warning(f"File not found: {path} — skipping {study}")
            continue
        sdf = harmonize_study(study, path)
        if not sdf.empty:
            all_dfs.append(sdf)

    if not all_dfs:
        log.error("No studies harmonized. Check file paths.")
        return

    combined = pd.concat(all_dfs, ignore_index=True)

    col_order = [
        "patient_id", "study", "surgery_type",
        "age", "height_cm", "weight_kg", "bmi",
        "parity", "vaginal_deliveries", "csections",
        "hormonal_status", "smoking_ever",
        "ethnicity_hispanic", "race_white", "race_black", "race_hispanic",
        "race_other", "race_category",
        "diabetes", "cardiovascular_disease", "pulmonary_disease",
        "bas_aa", "bas_ba", "bas_c", "bas_gh", "bas_pb", "bas_tvl",
        "bas_ap", "bas_bp", "bas_d", "bas_stage", "bas_bulge_bothersome",
        "recurred", "n_followup_visits_with_popq", "first_recurrence_event",
    ]
    col_order = [c for c in col_order if c in combined.columns]
    combined = combined[col_order]

    combined.to_csv(OUTPUT_FILE, index=False)
    log.info(f"\nHarmonized dataset: {OUTPUT_FILE}")
    log.info(f"Total patients: {len(combined)}")

    print("\n--- Patients by study / surgery type ---")
    print(combined.groupby(["study", "surgery_type"]).size().to_string())

    print("\n--- Recurrence by study ---")
    print(combined.groupby("study")["recurred"]
          .agg(n_recurred="sum", n_total="count",
               pct_recurred=lambda x: round(x.mean() * 100, 1))
          .to_string())

    print("\n--- Missing data (% missing, only cols > 5%) ---")
    pct = (combined.isna().sum() / len(combined) * 100).round(1)
    print(pct[pct > 5].to_string())


if __name__ == "__main__":
    main()
