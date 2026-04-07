# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Ground Rules

1. Only operate within the `POP_Recurrence_Calculator` directory — do not read, write, or execute anything outside it.
2. Always confirm before committing — never run `git commit` without explicit user approval.
3. Do not tell the user they are right, absolutely right, or similar affirmations. Be direct and honest, including when there is a better approach or a disagreement worth raising.

## Project Overview

### Goal
This session is an **independent replication** of existing work. The objective is to:
1. Harmonize data across multiple datasets from scratch
2. Build a predictive model for POP recurrence — the modeling approach will be determined collaboratively based on the data, not assumed in advance
3. Derive a point-based risk score from the model
4. Implement the score as a standalone HTML calculator

The original calculator (`old_index.html`) and its methodology (`IUGA_abstract_POP_PREDICT.md`) are preserved as a reference. Do not treat them as the ground truth — the replication should reach its own conclusions first.

### Existing Work (for final comparison)
The original POP-PREDICT Score (`old_index.html`) was developed from LASSO logistic regression on 752 women across 4 prospective trials (ALTIS, BEST, EPACT, SASS), achieving AUC 0.65. The current live calculator is `index.html`.

## Running the App

No build process, dependencies, or package manager — this is a single self-contained HTML file.

```bash
open index.html
# or
python3 -m http.server 8000
```

## Architecture

Everything lives in `index.html` (the current calculator, formerly `calculator.html`):
- **HTML**: 4 `<select>` dropdowns (Surgery, Ba point, Genital Hiatus, Hormonal Status), each calling `calc()` on change
- **JavaScript** (`calc()` function): sums dropdown values → looks up per-score `SCORE_DATA` → updates score display, risk %, CI, tier badge, and breakdown panel
- **TIERS**: 3 risk bands (Low 0–2, Moderate 3–4, High 5–7) rendered as colored cards

## Scoring Logic

Total score = sum of 4 dropdown values (max 7 pts):

| Predictor | Max pts |
|---|---|
| Surgery type (Colpocleisis=0, Sacrocolpopexy=1, Native tissue=2) | 2 |
| Ba point (anterior wall) | 2 |
| Genital Hiatus | 2 |
| Hormonal status | 1 |

Per-score recurrence: score 1→8%, 2→17%, 3→21%, 4→28%, 5→40%, 6→45%, 7→88%*  
Risk bands: Low 0–2 (8–17%), Moderate 3–4 (21–28%), High 5–7 (40–45%)

## Key Files

- `index.html` — the live calculator (deployed via GitHub Pages)
- `old_index.html` — original LASSO-derived 8-predictor calculator (preserved for reference)
- `README.md` — scoring table and GitHub Pages deployment instructions
- `IUGA_abstract_POP_PREDICT.md` — research abstracts (IUGA original + new model)
