# Data Harmonization Decisions
**Project:** POP-PREDICT Score — Independent Replication  
**Branch:** marie_data  
**Author:** Claude (claude-sonnet-4-6), supervised by Marie Sullivan, MD

This document is the authoritative record of every decision made during data harmonization. It is intended to be submitted as a methods supplement to an academic journal and to allow full reproducibility. All decisions confirmed by M. Sullivan unless noted otherwise.

---

## 1. Studies Included

| Study | File | Surgery Type | N (approx) | Follow-up |
|-------|------|-------------|------------|-----------|
| ALTIS | `ALTIS_DATA_LABELS_2025-10-02_1054.csv` | Native tissue vaginal repair or colpocleisis | ~300 | 6wk, 12mo, 2yr, 3yr |
| BEST | `BEST_DATA_LABELS_2025-10-02_1045.csv` | Robotic sacrocolpopexy (barbed vs nonbarbed suture RCT) | ~52 | 6wk, 6mo, 12mo |
| EPACT | `EPACT_DATA_LABELS_2025-10-02_1057.csv` | Robotic/laparoscopic sacrocolpopexy | ~unknown | 6wk, 6mo, 1yr, 2yr, 3yr |
| SASS | `SASS_DATA_LABELS_2025-10-02_1051.csv` | Sacrocolpopexy (all types) | ~unknown | 6wk, 12mo, 3yr, 5yr |
| ELOVE | `ELOVE_DATA_LABELS_2025-10-02_1048.csv` | None (natural history comparator) | ~unknown | Multiple |

**Decision:** ELOVE patients had no prolapse surgery. They are included as a natural history group with `surgery_type = 'none'`. Their follow-up POP-Q measurements track the natural course of prolapse without surgical intervention. Confirmed by M. Sullivan.

**Decision:** PACT and EPACT refer to the same study. The data file is labeled EPACT. Confirmed by M. Sullivan.

**Decision:** ELOVE patients are included in the harmonized dataset. They will not be used as outcome cases in the main model but will supplement demographic representation and serve as a natural history reference. Confirmed by M. Sullivan.

---

## 2. Primary Outcome: Composite Recurrence

**Definition (confirmed by M. Sullivan, replicating existing work):**  
A patient is considered to have prolapse recurrence if, at **any follow-up visit with POP-Q data**, they meet **at least one** of the following criteria:

1. **Anatomic (stage):** POP-Q Stage ≥ 2
2. **Anatomic (point):** Any POP-Q measurement point (Aa, Ba, C, Ap, Bp) ≥ 0
3. **Symptomatic:** Bothersome vaginal bulge on PFDI-20 Question 3 (score ≥ 2, i.e., "Somewhat," "Moderately," or "Quite a bit")

**Note on EPACT PFDI-20 format:** EPACT uses a two-part PFDI-20 format for Q3:
- `pfdi_3`: "Do you usually have a bulge...?" (0=No, 1=Yes)
- `pfdi_3_a`: "If yes, how much does this bother you?" (0=Not at All, 1=Somewhat, 2=Moderately, 3=Quite a bit)

Bothersome bulge in EPACT is defined as `pfdi_3 == 1 AND pfdi_3_a >= 1`, which is equivalent to a score ≥ 2 in other studies' single-question format.

**Note on minimum follow-up:** No minimum follow-up duration is required for inclusion. Patients are included regardless of how few follow-up visits they completed. Confirmed by M. Sullivan.

**Note on baseline measurements:** The composite criteria are applied to **follow-up** POP-Q measurements only. Baseline POP-Q reflects pre-operative status and is not used as an outcome measurement.

**For ELOVE (no surgery):** The composite criteria are applied to follow-up measurements to characterize the natural history of untreated prolapse. Their recurrence indicator is interpretable as "prolapse meeting criteria at follow-up" rather than post-operative recurrence.

---

## 3. Surgery Type Classification

Surgery type is derived per study as follows:

- **SASS:** All patients = `sacrocolpopexy` (by study design)
- **BEST:** All patients = `sacrocolpopexy` (by study design; randomization is suture type, not procedure type)
- **EPACT:** All patients = `sacrocolpopexy` (by study design)
- **ELOVE:** All patients = `none` (no prolapse surgery by study design)
- **ALTIS:** Derived from the surgical procedure checkbox field. Patients with colpocleisis checked (`Prolapse Procedures: (choice=colpoclesis)` == "Checked") = `colpocleisis`. All others = `native_tissue`.

**Note:** BEST's randomization variable (`randomization`: 0=V-LoC barbed suture, 1=PDS nonbarbed suture) is an intra-operative technical variable and is NOT included in the recurrence model.

---

## 4. Variable Mapping

### 4a. Event Names by Study (Baseline and Follow-up)

| Study | Baseline Event | Follow-up Events with POP-Q |
|-------|---------------|----------------------------|
| ALTIS | `Baseline` | `6 Week Follow-Up`, `12 Month Follow-Up`, and longer-term events |
| SASS | `Baseline Visit` | Events containing `w6_popq_stage`, `m12_popq_stage`, `yr3_popq_stage_v9`, `yr5_popq_stage_v11` |
| BEST | `Baseline` | `6WK Visit`, `6M Visit`, `12M Visit` |
| EPACT | `Baseline` | `Week 6 follow up`, `Month 6 follow up`, `Year 1 follow up`, `EPACT Year 2+ follow up`, `EPACT Year 3+ follow up` |
| ELOVE | `Baseline` | All non-baseline events |

**Implementation note:** Rather than filtering strictly by event name, the script scans all non-baseline rows for any non-null POP-Q values in any known follow-up POP-Q column. This is more robust to event naming variations.

### 4b. Baseline POP-Q Variable Names

| Point | ALTIS / SASS / BEST | EPACT |
|-------|---------------------|-------|
| Aa | `bas_popq_aa` | `bl_aa` |
| Ba | `bas_popq_ba` | `bl_ba` |
| C | `bas_popq_c` | `bl_c` |
| gh | `bas_popq_gh` | `bl_gh` |
| pb | `bas_popq_pb` | `bl_pb` |
| tvl | `bas_popq_tvl` | `bl_tvl` |
| Ap | `bas_popq_ap` | `bl_ap` |
| Bp | `bas_popq_bp` | `bl_bp` |
| D | `bas_popq_d` | (not collected) |
| Stage | `bas_popq_stage` | `bl_popq_stage` |

### 4c. Follow-up POP-Q Variable Names (scanned across all event rows)

| Timepoint | ALTIS / SASS | BEST | EPACT |
|-----------|-------------|------|-------|
| 6-week | `w6_popq_aa/ba/c/ap/bp/stage` | `aa/ba/c/ap/bp/popq_stage` | `w6_aa/ba/c/ap/bp`, `w6_popq_stage` |
| 12-month | `m12_popq_aa/ba/c/ap/bp/stage` | `aa/ba/c/ap/bp/popq_stage` | `y1_aa/ba/c/ap/bp`, `y1_popq_stage` |
| 3-year | `yr3_popq_aa/ba/c/ap/bp_v9`, `yr3_popq_stage_v9` | — | `EPACT Year 2+/3+ follow up` events |
| 5-year | `yr5_popq_aa/ba/c/ap/bp_v11`, `yr5_popq_stage_v11` | — | — |

**Implementation note:** BEST uses the same follow-up POP-Q variable names (`aa`, `ba`, `c`, `ap`, `bp`, `popq_stage`) across 6-week, 6-month, and 12-month visits, distinguished by the `Event Name` column.

### 4d. Bothersome Bulge Symptom Variable Names

| Study | Variable | Coding | Threshold |
|-------|---------|--------|-----------|
| ALTIS | `pfdi3` | 0=No, 1=Not at all, 2=Somewhat, 3=Moderately, 4=Quite a bit | ≥ 2 |
| SASS | `popdi6_b_3_v2` | 0=No, 1=doesn't bother, 2=somewhat, 3=moderately, 4=quite a bit | ≥ 2 |
| BEST | To be determined from data | — | ≥ 2 (expected) |
| EPACT | `pfdi_3` + `pfdi_3_a` | pfdi_3: 0=No/1=Yes; pfdi_3_a: 0=Not at All/1=Somewhat/2=Moderately/3=Quite a bit | pfdi_3==1 AND pfdi_3_a≥1 |
| ELOVE | To be determined from data | — | ≥ 2 (expected) |

### 4e. Demographic Variable Names

| Variable | ALTIS / SASS / BEST (partial) | EPACT | Notes |
|----------|-------------------------------|-------|-------|
| Age | `bas_age` | `bl_age` | |
| Height (cm) | `bas_height` | `bl_height` | |
| Weight (kg) | `bas_weight` | `bl_weight` | |
| Parity | `bas_medhist1` | `bl_parity` | |
| Vaginal deliveries | `bas_medhist2` | `bl_vag_parity` | |
| C-sections | `bas_medhist3` | `bl_caesarean_parity` | |
| Hormonal status | `bas_medhist4` (1–4) | `bl_horm_status` (0–3) | See §4f |
| Race | `bas_race` (checkbox 1-6) | `bl_race` (checkbox 0-5) | See §4g |
| Ethnicity | `bas_ethn` | `bl_ethnicity` | See §4h |
| Smoking | `bas_medhist5` | Not found in EPACT dict | See §4i |
| Diabetes | `co_morb13` or `co_morb14` | same | YES in either = diabetic |
| Cardiovascular | `co_morb2/3/4/5` | same | YES in any = CVD |
| Pulmonary (COPD) | `co_morb7` | same | |

### 4f. Hormonal Status Harmonization

| Label | ALTIS/SASS/BEST code | EPACT code | Harmonized code |
|-------|---------------------|------------|-----------------|
| Pre or Peri-menopausal | 1 | 0 | 0 |
| Postmenopausal, No HRT | 2 | 1 | 1 |
| Postmenopausal, Vaginal estrogen | 3 | 2 | 2 |
| Postmenopausal, Oral/systemic HRT | 4 | 3 | 3 |

Hormonal status is retained as a 4-level categorical variable in the harmonized dataset. Pre/peri-menopausal (0) is a clinically distinct group from postmenopausal-no-HRT (1) and must not be collapsed. No binary HRT indicator is pre-computed; any such collapsing will be done at modeling time if needed. Confirmed by M. Sullivan.

### 4g. Race Harmonization

All studies use multi-select checkbox race fields. Race is harmonized into a single categorical variable using the following priority:
1. If ethnicity = Hispanic → `race_category = 'Hispanic'`
2. Else if White/Caucasian selected → `race_category = 'White'`
3. Else if Black/African American selected → `race_category = 'Black'`
4. Else → `race_category = 'Other'`

**Decision rationale:** This matches the existing calculator's race variable which groups: White, Black (1 pt) vs. Hispanic or Other (0 pts). We retain detailed indicator columns (`race_white`, `race_black`, `race_hispanic`, `race_other`) for exploratory analysis.

**EPACT race coding differences:**
- EPACT `bl_race`: 0=Caucasian, 1=Black/AA, 2=Asian, 3=Native Hawaiian/PI, 4=Native American/AN, 5=Other
- Other studies `bas_race`: 1=Asian, 2=Black/AA, 3=Native American/AN, 4=Native Hawaiian/PI, 5=White/Caucasian, 6=Other

### 4h. Ethnicity Harmonization

- ALTIS/SASS/BEST: `bas_ethn` = "Hispanic or Latino" | "Neither Hispanic Nor Latino"  
- EPACT: `bl_ethnicity` = 1 (Hispanic) or 0 (Not Hispanic)

Harmonized to `ethnicity_hispanic` = 1 (Hispanic) / 0 (Not Hispanic).

### 4i. Smoking

- ALTIS/SASS: `bas_medhist5` — 1=Never, 2=Previous, 3=Current  
- BEST: `bas_smoke` — similar coding  
- EPACT: No dedicated smoking variable found in data dictionary; Charlson index does not include smoking. Smoking will be set to missing for EPACT patients.

Harmonized to `smoking_ever` = 1 (Previous or Current) / 0 (Never) / NaN (unknown).

---

## 5. Globally Unique Patient ID

Study ID fields are not globally unique across studies (e.g., SASS and ELOVE both use "1-001" format). A globally unique patient ID is created as:

```
patient_id = f"{study_prefix}_{original_study_id}"
```

| Study | Prefix | Example |
|-------|--------|---------|
| ALTIS | `ALTIS` | `ALTIS_A001` |
| BEST | `BEST` | `BEST_CAM001` |
| EPACT | `EPACT` | `EPACT_A001` |
| SASS | `SASS` | `SASS_1-001` |
| ELOVE | `ELOVE` | `ELOVE_1-001` |

---

## 6. BMI Calculation

BMI is calculated as `weight_kg / (height_cm / 100)^2` for all studies. EPACT provides a pre-calculated `bl_bmi` field; we recalculate from raw values for consistency.

---

## 7. Output Schema

The harmonized dataset (`data/harmonized_data.csv`) contains one row per patient with the following columns:

**Identity:** `patient_id`, `study`, `surgery_type`  
**Demographics:** `age`, `height_cm`, `weight_kg`, `bmi`, `parity`, `vaginal_deliveries`, `csections`, `hormonal_status`, `smoking_ever`, `ethnicity_hispanic`  
**Race indicators:** `race_white`, `race_black`, `race_hispanic`, `race_other`, `race_category`  
**Comorbidities:** `diabetes`, `cardiovascular_disease`, `pulmonary_disease`  
**Baseline POP-Q:** `bas_aa`, `bas_ba`, `bas_c`, `bas_gh`, `bas_pb`, `bas_tvl`, `bas_ap`, `bas_bp`, `bas_d`, `bas_stage`  
**Baseline symptom:** `bas_bulge_bothersome`  
**Outcome:** `recurred`, `n_followup_visits_with_popq`, `first_recurrence_event`

---

## 8. Change Log

| Date | Decision | Confirmed By |
|------|----------|-------------|
| 2026-04-06 | PACT = EPACT (same study) | M. Sullivan |
| 2026-04-06 | Outcome = composite (Stage ≥2, any point ≥0, bothersome bulge) | M. Sullivan |
| 2026-04-06 | Apply recurrence criteria at any follow-up timepoint | M. Sullivan |
| 2026-04-06 | No minimum follow-up threshold | M. Sullivan |
| 2026-04-06 | ELOVE = natural history group, surgery_type = none, do not exclude | M. Sullivan |
| 2026-04-06 | Modeling approach to be determined collaboratively (not pre-specified as LASSO) | M. Sullivan |
| 2026-04-06 | Pre/peri-menopausal hormonal status is its own level (0); not collapsed with postmenopausal-no-HRT; no binary on_hrt variable computed | M. Sullivan |
| 2026-04-06 | Stage ≥2 retained as recurrence threshold; Stage 2 is clinically appropriate lower bound | M. Sullivan |
| 2026-04-06 | 6-week visit excluded from recurrence assessment IF the patient has any later follow-up with outcome data; retained as last known observation if it is the patient's only outcome data point | M. Sullivan |
