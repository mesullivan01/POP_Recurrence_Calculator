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

The existing calculator (`index.html`) and its methodology (`IUGA_abstract_POP_PREDICT.md`) are preserved as a reference to compare against at the end. Do not treat them as the ground truth during development — the replication should reach its own conclusions first.

### Existing Work (for final comparison)
The POP-PREDICT Score is a single-file clinical decision-support tool (`index.html`) for estimating pelvic organ prolapse (POP) recurrence risk after surgical repair. It was developed from LASSO logistic regression on 752 women across 4 prospective trials (ALTIS, BEST, EPACT, SASS), achieving AUC 0.65.

## Running the App

No build process, dependencies, or package manager — this is a single self-contained HTML file.

```bash
open index.html
# or
python3 -m http.server 8000
```

## Architecture

Everything lives in `index.html`:
- **CSS** (`:root` design tokens → component styles): teal/amber/coral/red color scheme maps directly to Low/Moderate/High/Very High risk tiers
- **HTML**: 8 `<select>` dropdowns (one per predictor), each calling `calc()` on change
- **JavaScript** (`calc()` function): sums all `select.value` integers → looks up the matching stratum → updates DOM (score display, progress bar, active stratum card, border colors)

## Scoring Logic

Total score = sum of all 8 dropdown values (max 14 pts):

| Predictor | Max pts |
|---|---|
| Surgery type (Colpocleisis=0, Sacrocolpopexy=1, USLS/SSLF=2) | 2 |
| Ba point (anterior wall) | 3 |
| C point (apical) | 2 |
| Aa point (anterior) | 1 |
| Parity | 2 |
| Height | 2 |
| Hormonal status | 1 |
| Race | 1 |

Risk strata: 0–4 pts (~10%), 5–7 (~25%), 8–10 (~40%), 11–14 (~55%)

## Key Files

- `index.html` — the entire application
- `README.md` — scoring table and GitHub Pages deployment instructions
- `IUGA_abstract_POP_PREDICT.md` — underlying research abstract with model performance details and patient cohort data
