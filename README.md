# POP-PREDICT Score

**Prolapse Recurrence Risk Calculator**  
Sullivan M, Kim S, El Haraki A · Atrium Health Wake Forest Baptist

---

## Overview

The POP-PREDICT Score is a clinical decision-support tool for estimating the risk of pelvic organ prolapse (POP) recurrence following surgical repair. It incorporates 8 predictors selected via LASSO logistic regression from a pooled analysis of 752 women across 4 prospective trials (ALTIS, BEST, EPACT, SASS).

**Model performance:** AUC 0.65 · Sensitivity 0.58 · Specificity 0.72 · PPV 0.41 · NPV 0.83  
Validated with 5-fold cross-validation and leave-one-dataset-out (LODO) external validation.

---

## Scoring Variables

| Variable | Criteria | Points |
|---|---|---|
| **Surgery type** | Colpocleisis | 0 |
| | Sacrocolpopexy | 1 |
| | USLS / SSLF | 2 |
| **Ba point (anterior wall)** | < 0 cm | 0 |
| | 0–2 cm | 1 |
| | 3–4 cm | 2 |
| | > 4 cm | 3 |
| **Parity** | 0–1 births | 0 |
| | 2–3 births | 1 |
| | ≥ 4 births | 2 |
| **Height** | < 160 cm | 0 |
| | 160–168 cm | 1 |
| | > 168 cm | 2 |
| **C point (apical)** | < −4 cm | 0 |
| | −4 to 0 cm | 1 |
| | > 0 cm | 2 |
| **Hormonal status** | On HRT | 0 |
| | No HRT | 1 |
| **Aa point (anterior)** | ≤ 0 cm | 0 |
| | > 0 cm | 1 |
| **Race** | Hispanic or other | 0 |
| | White or Black | 1 |

**Total: 0–14 points**

---

## Risk Stratification

| Score | Risk Category | Recurrence Probability |
|---|---|---|
| 0–4 | Low | ~10% |
| 5–7 | Moderate | ~25% |
| 8–10 | High | ~40% |
| 11–14 | Very High | ~55% |

---

## Usage

This is a single-file web app (`index.html`) — no build process or dependencies required.

### Run locally
```bash
open index.html
```
Or serve with any static file server:
```bash
python3 -m http.server 8000
```

### Deploy to GitHub Pages (free hosting)
1. Push this repository to GitHub
2. Go to **Settings → Pages**
3. Set source to **main branch / root folder**
4. Your calculator will be live at `https://yourusername.github.io/POP_Recurrence_Calculator`

---

## Abbreviations

- **USLS** — Uterosacral ligament suspension  
- **SSLF** — Sacrospinous ligament fixation  
- **HRT** — Hormone replacement therapy  
- **POP-Q** — Pelvic Organ Prolapse Quantification system  
- **LASSO** — Least Absolute Shrinkage and Selection Operator  
- **LODO** — Leave-one-dataset-out

---

## Disclaimer

This tool is intended to support preoperative counseling and shared decision-making. It does not replace clinical judgment. For research and educational use.

---

## Citation

Sullivan M, Kim S, El Haraki A. *Development of the POP-PREDICT Score: A Machine Learning-Derived Prediction Calculator for Recurrence Risk in Pelvic Organ Prolapse Surgery.* Atrium Health Wake Forest Baptist, 2025.
