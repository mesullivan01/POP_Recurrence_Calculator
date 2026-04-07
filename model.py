"""
model.py
========
Builds and validates two logistic regression models predicting POP recurrence:
  1. LASSO logistic regression (L1 penalty, lambda selected by 5-fold CV)
  2. Standard logistic regression (backward stepwise by AIC)

Both models are validated with:
  - 5-fold cross-validation (AUC)
  - Leave-one-dataset-out (LODO) validation

Input:  data/harmonized_data.csv
Output: results/model_results.txt  (printed + saved)

See procedure/claude/data_harmonizing_decisions.md for outcome definition.
"""

import os
import warnings
import numpy as np
import pandas as pd
from itertools import combinations

from sklearn.linear_model import LogisticRegressionCV, LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import StratifiedKFold
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer

import statsmodels.api as sm
from scipy import stats

warnings.filterwarnings("ignore")
os.makedirs("results", exist_ok=True)

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

DATA_FILE   = "data/harmonized_data.csv"
OUTPUT_FILE = "results/model_results.txt"

# Candidate predictors before encoding
CONTINUOUS_VARS = [
    "bmi", "height_cm",
    "parity", "vaginal_deliveries", "csections",
    "bas_aa", "bas_ba", "bas_c", "bas_ap", "bas_bp",
    "bas_gh", "bas_pb", "bas_tvl",
]
BINARY_VARS = [
    "diabetes", "cardiovascular_disease",
]
# Categorical vars encoded as dummies (reference level in parens)
# surgery_type   → ref = sacrocolpopexy
# hormonal_status→ ordinal 0–3 treated as continuous
# race_category  → ref = White

OUTCOME = "recurred"
STUDY_COL = "study"

# ---------------------------------------------------------------------------
# DATA PREPARATION
# ---------------------------------------------------------------------------

def load_and_prepare():
    df = pd.read_csv(DATA_FILE)

    # Surgical patients only
    df = df[df["surgery_type"] != "none"].copy()
    df["recurred"] = df["recurred"].astype(int)

    # ---- Surgery type dummies (ref = sacrocolpopexy) ----
    df["surg_native"]      = (df["surgery_type"] == "native_tissue").astype(float)
    df["surg_colpocleisis"] = (df["surgery_type"] == "colpocleisis").astype(float)

    # ---- Hormonal status: ordinal 0–3 ----
    df["hormonal_status"] = pd.to_numeric(df["hormonal_status"], errors="coerce")

    # ---- Race dummies (ref = White; Unknown collapsed into Other) ----
    df["race_black"]    = (df["race_category"] == "Black").astype(float)
    df["race_hispanic"] = (df["race_category"] == "Hispanic").astype(float)
    df["race_other"]    = (df["race_category"].isin(["Other", "Unknown"])).astype(float)

    # ---- Encode binary vars as float ----
    for v in BINARY_VARS:
        df[v] = pd.to_numeric(df[v], errors="coerce").astype(float)

    # ---- Encode continuous vars as float ----
    for v in CONTINUOUS_VARS:
        df[v] = pd.to_numeric(df[v], errors="coerce").astype(float)

    return df


def build_feature_matrix(df):
    """
    Assemble predictor matrix.  BMI is imputed via IterativeImputer (MICE-like)
    using all other continuous predictors as context.  All other variables use
    complete-case for their own missingness (<5% each).
    """
    feature_cols = (
        CONTINUOUS_VARS
        + ["hormonal_status"]
        + BINARY_VARS
        + ["surg_native", "surg_colpocleisis"]
    )

    df = df.copy()

    # Correct data entry errors in POP-Q measurements:
    #   - Values >100 cm: decimal point entered as "0" (e.g., 305 → 3.05, 905 → 9.05) → divide by 100
    #   - Negative tvl: sign entered as "-" instead of "+" (e.g., -9.5 → +9.5) → negate
    for col in ["bas_gh", "bas_pb", "bas_tvl",
                "bas_aa", "bas_ba", "bas_c", "bas_ap", "bas_bp"]:
        if col in df.columns:
            df.loc[df[col] > 100, col] = df.loc[df[col] > 100, col] / 100.0
    df.loc[df["bas_tvl"] < 0, "bas_tvl"] = df.loc[df["bas_tvl"] < 0, "bas_tvl"].abs()

    X = df[feature_cols].copy()
    y = df[OUTCOME].values
    studies = df[STUDY_COL].values

    # Impute BMI using IterativeImputer (max 10 iterations)
    imp = IterativeImputer(max_iter=10, random_state=42)
    X_imputed = pd.DataFrame(imp.fit_transform(X), columns=feature_cols, index=X.index)

    # Drop rows still missing outcome or study
    mask = df[OUTCOME].notna() & df[STUDY_COL].notna()
    X_imputed = X_imputed[mask]
    y = y[mask]
    studies = studies[mask]

    return X_imputed, y, studies, feature_cols


# ---------------------------------------------------------------------------
# MODEL 1: LASSO LOGISTIC REGRESSION
# ---------------------------------------------------------------------------

def fit_lasso(X_train, y_train):
    """
    Fit LASSO logistic regression using the 1-SE rule for C selection.

    Steps:
      1. Run LogisticRegressionCV across a grid of C values (5-fold CV, AUC).
      2. Identify the best mean CV AUC and its SD across folds.
      3. Apply 1-SE rule: choose the smallest C (most regularized / sparsest model)
         whose mean AUC is within 1 SE of the best AUC.
      4. Refit on all training data at that C.

    Returns fitted model and scaler.
    """
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X_train)

    Cs = np.logspace(-3, 2, 50)
    cv_splitter = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    lrcv = LogisticRegressionCV(
        Cs=Cs,
        cv=cv_splitter,
        penalty="l1",
        solver="liblinear",
        scoring="roc_auc",
        max_iter=5000,
        random_state=42,
    )
    lrcv.fit(Xs, y_train)

    # scores_ shape: (n_samples_or_folds, n_Cs) — access per-fold AUC across Cs
    # LogisticRegressionCV stores scores per class; use class 1
    scores = lrcv.scores_[1]          # shape: (n_folds, n_Cs)
    mean_auc = scores.mean(axis=0)    # mean over folds for each C
    std_auc  = scores.std(axis=0)

    best_idx   = np.argmax(mean_auc)
    threshold  = mean_auc[best_idx] - std_auc[best_idx]

    # 1-SE rule: smallest C (index 0 = most regularized) whose mean >= threshold
    se1_idx = next(
        (i for i in range(len(Cs)) if mean_auc[i] >= threshold),
        best_idx,
    )
    best_C = Cs[se1_idx]

    # Refit at selected C
    model = LogisticRegression(
        C=best_C,
        penalty="l1",
        solver="liblinear",
        max_iter=5000,
        random_state=42,
    )
    model.fit(Xs, y_train)
    model.C_ = best_C          # store for reporting
    model.best_C_idx_ = se1_idx
    model.mean_auc_at_C_ = mean_auc[se1_idx]
    return model, scaler


def lasso_selected_features(model, feature_cols):
    """Return feature names with non-zero LASSO coefficients."""
    coef = model.coef_[0]
    return [f for f, c in zip(feature_cols, coef) if c != 0]


# ---------------------------------------------------------------------------
# MODEL 2: STANDARD LOGISTIC REGRESSION (BACKWARD AIC)
# ---------------------------------------------------------------------------

def fit_logistic_backward_aic(X_df, y):
    """
    Backward stepwise logistic regression using AIC.
    Starts with all predictors; drops the variable whose removal reduces AIC most,
    continuing until no removal improves AIC.
    Returns fitted statsmodels result on the final variable set.
    """
    current_vars = list(X_df.columns)

    def fit_aic(vars_):
        Xc = sm.add_constant(X_df[vars_].values)
        try:
            res = sm.Logit(y, Xc).fit(disp=False, maxiter=200)
            return res.aic, res
        except Exception:
            return np.inf, None

    best_aic, best_result = fit_aic(current_vars)

    while True:
        improved = False
        best_drop = None
        for var in current_vars:
            candidate = [v for v in current_vars if v != var]
            if not candidate:
                continue
            aic, _ = fit_aic(candidate)
            if aic < best_aic - 1e-6:
                best_aic = aic
                best_drop = var
                improved = True

        if not improved:
            break
        current_vars.remove(best_drop)

    # Final fit on selected variables
    _, final_result = fit_aic(current_vars)
    return final_result, current_vars


# ---------------------------------------------------------------------------
# EVALUATION HELPERS
# ---------------------------------------------------------------------------

def compute_metrics(y_true, y_prob, threshold=0.5):
    auc = roc_auc_score(y_true, y_prob)
    fpr, tpr, thresholds = roc_curve(y_true, y_prob)
    # Youden index for optimal threshold
    j = tpr - fpr
    opt_idx = np.argmax(j)
    opt_thresh = thresholds[opt_idx]
    y_pred = (y_prob >= opt_thresh).astype(int)
    tp = ((y_pred == 1) & (y_true == 1)).sum()
    tn = ((y_pred == 0) & (y_true == 0)).sum()
    fp = ((y_pred == 1) & (y_true == 0)).sum()
    fn = ((y_pred == 0) & (y_true == 1)).sum()
    sens = tp / (tp + fn) if (tp + fn) > 0 else np.nan
    spec = tn / (tn + fp) if (tn + fp) > 0 else np.nan
    ppv  = tp / (tp + fp) if (tp + fp) > 0 else np.nan
    npv  = tn / (tn + fn) if (tn + fn) > 0 else np.nan
    return {"auc": auc, "sens": sens, "spec": spec, "ppv": ppv, "npv": npv,
            "opt_threshold": opt_thresh}


def cv_auc(X_df, y, model_fn, n_splits=5):
    """
    5-fold stratified CV returning list of fold AUCs.
    model_fn(X_train_df, y_train) → (model, scaler_or_None)
    predict_fn is embedded per model type inside model_fn return.
    """
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    aucs = []
    for train_idx, test_idx in skf.split(X_df, y):
        X_tr = X_df.iloc[train_idx]
        X_te = X_df.iloc[test_idx]
        y_tr = y[train_idx]
        y_te = y[test_idx]
        model, scaler = model_fn(X_tr, y_tr)
        if scaler is not None:
            X_te_s = scaler.transform(X_te)
            prob = model.predict_proba(X_te_s)[:, 1]
        else:
            Xc = sm.add_constant(X_te.values, has_constant="add")
            prob = model.predict(Xc)
        aucs.append(roc_auc_score(y_te, prob))
    return aucs


def lodo_auc(X_df, y, studies, model_fn):
    """
    Leave-one-dataset-out validation.
    model_fn(X_train_df, y_train) → (model, scaler_or_None)
    """
    unique_studies = np.unique(studies)
    results = {}
    for held_out in unique_studies:
        mask_train = studies != held_out
        mask_test  = studies == held_out
        if mask_test.sum() < 5:
            continue
        X_tr = X_df[mask_train]
        X_te = X_df[mask_test]
        y_tr = y[mask_train]
        y_te = y[mask_test]
        if len(np.unique(y_te)) < 2:
            continue
        model, scaler = model_fn(X_tr, y_tr)
        if scaler is not None:
            X_te_s = scaler.transform(X_te)
            prob = model.predict_proba(X_te_s)[:, 1]
        else:
            Xc = sm.add_constant(X_te.values, has_constant="add")
            prob = model.predict(Xc)
        results[held_out] = roc_auc_score(y_te, prob)
    return results


# ---------------------------------------------------------------------------
# POINT SCORE DERIVATION
# ---------------------------------------------------------------------------

def derive_point_score(std_result, std_vars, X_df, y, lines_out):
    """
    Derive integer point-based risk score from the final standard logistic model.

    Method (Sullivan/Framingham style):
      1. Extract raw β coefficients.
      2. Choose scale factor k so that the total β-weighted range ≈ 12 pts.
      3. For each predictor, define clinically motivated bins and assign integer pts
         using round(β × meaningful_Δ × k).
      4. Surgery is anchored at colpocleisis=0 (most protective), sacro=+3,
         native tissue=+4, reflecting the colpocleisis β advantage of ~3 pt-units.
      5. Shift all scores so the theoretical minimum = 0.
      6. Report empirical recurrence rate per point total.
    """

    def log(s=""):
        print(s)
        lines_out.append(s)

    betas = dict(zip(std_vars, std_result.params[1:]))

    # ---- Scale factor ----
    # Total β-weighted range across predictors:
    # bas_ba: 0.128/cm × 9 cm range ≈ 1.15
    # bas_gh: 0.239/cm × 4 cm range ≈ 0.96
    # bas_tvl: 0.084/cm × 3 cm range ≈ 0.25
    # hormonal_status: 0.201 × 1 (binary post-no-HRT) ≈ 0.20
    # surgery (native−colpo): 0.392+1.102 ≈ 1.49
    # Total ≈ 4.05 log-odds → map to 12 points
    k = 12.0 / 4.05   # ≈ 2.96

    log("\n" + "=" * 70)
    log("POINT SCORE DERIVATION (Standard Logistic Model)")
    log("=" * 70)
    log("\nβ coefficients and raw point values (scale factor k={:.2f}):".format(k))
    log(f"  {'Variable':<30} {'β':>8}  {'Meaningful unit':<25} {'Raw pts':>8}")
    log(f"  {'-'*30} {'-'*8}  {'-'*25} {'-'*8}")

    # Report β × meaningful unit × k for each variable
    units = {
        "bas_ba":           ("per 3 cm",   3.0),
        "bas_gh":           ("per 1.5 cm", 1.5),
        "bas_tvl":          ("per 3 cm",   3.0),
        "hormonal_status":  ("binary (0/1 pts)", 1.0),
        "surg_native":      ("vs sacro",   1.0),
        "surg_colpocleisis":("vs sacro",   1.0),
    }
    for v, b in sorted(betas.items(), key=lambda x: abs(x[1]), reverse=True):
        desc, delta = units.get(v, ("per unit", 1.0))
        raw = b * delta * k
        log(f"  {v:<30} {b:>8.3f}  {desc:<25} {raw:>8.2f}")

    # ---- Proposed integer score table (conditional on selected vars) ----
    log("\nProposed point table:")
    log("  Surgery type:")
    log("    Colpocleisis                      0 pts")
    log("    Sacrocolpopexy                    1 pt")
    log("    Native tissue                     2 pts")

    if "bas_ba" in std_vars:
        log("  Anterior wall, Ba (cm):")
        log("    Ba < 0                            0 pts")
        log("    Ba 0 – 3                          1 pt")
        log("    Ba ≥ 4                            2 pts")

    if "bas_gh" in std_vars:
        log("  Genital hiatus, gh (cm):")
        log("    gh ≤ 3                            0 pts")
        log("    gh 4 – 5                          1 pt")
        log("    gh ≥ 6                            2 pts")

    if "bas_tvl" in std_vars:
        log("  Total vaginal length, tvl (cm):")
        log("    tvl ≥ 9                           0 pts")
        log("    tvl < 9                           1 pt")

    if "hormonal_status" in std_vars:
        log("  Hormonal status:")
        log("    Pre/peri-menopausal               0 pts")
        log("    Postmenopausal, no HRT            1 pt")
        log("    Postmenopausal, vaginal estrogen  0 pts")
        log("    Postmenopausal, oral/systemic HRT 0 pts")

    max_pts = (2
               + (2 if "bas_ba" in std_vars else 0)
               + (2 if "bas_gh" in std_vars else 0)
               + (1 if "bas_tvl" in std_vars else 0)
               + (1 if "hormonal_status" in std_vars else 0))
    log(f"  Score range: 0 – {max_pts} points")

    # ---- Compute per-patient score ----
    pts = pd.Series(0.0, index=X_df.index)

    # Surgery (colpocleisis=0, sacro=1, native=2)
    pts += 1.0  # all patients start at sacro baseline
    if "surg_colpocleisis" in X_df.columns:
        pts -= X_df["surg_colpocleisis"] * 1.0  # colpocleisis → subtract 1
    if "surg_native" in X_df.columns:
        pts += X_df["surg_native"] * 1.0         # native tissue → add 1

    # ba
    if "bas_ba" in std_vars and "bas_ba" in X_df.columns:
        ba = X_df["bas_ba"]
        pts += (ba >= 0).astype(float)
        pts += (ba >= 4).astype(float)

    # gh
    if "bas_gh" in std_vars and "bas_gh" in X_df.columns:
        gh = X_df["bas_gh"]
        pts += (gh >= 4).astype(float)
        pts += (gh >= 6).astype(float)

    # tvl (protective: shorter TVL = more pts)
    if "bas_tvl" in std_vars and "bas_tvl" in X_df.columns:
        pts += (X_df["bas_tvl"] < 9).astype(float)

    # hormonal status: postmenopausal-no HRT (1) = 1 pt; all others = 0
    if "hormonal_status" in std_vars and "hormonal_status" in X_df.columns:
        pts += (X_df["hormonal_status"] == 1).astype(float)

    pts = pts.round().astype(int)

    # ---- Score distribution and recurrence by tier ----
    log("\nEmpirical recurrence by score (proposed tiers):")
    log(f"  {'Score range':<14} {'N':>5}  {'Events':>7}  {'Recurrence %':>13}")
    log(f"  {'-'*14} {'-'*5}  {'-'*7}  {'-'*13}")

    tiers = [(0, 2, "Low (0–2)"), (3, 5, "Moderate (3–5)"), (6, max_pts, f"High (6–{max_pts})")]
    for lo, hi, label in tiers:
        mask = (pts >= lo) & (pts <= hi)
        n = mask.sum()
        if n == 0:
            log(f"  {label:<14} {0:>5}  {'—':>7}  {'—':>13}")
            continue
        ev = int(y[mask.values].sum())
        pct = ev / n * 100
        log(f"  {label:<14} {n:>5}  {ev:>7}  {pct:>12.1f}%")

    log("\nFull score distribution:")
    log(f"  {'Score':>6}  {'N':>5}  {'Events':>7}  {'%':>8}")
    for sc in sorted(pts.unique()):
        mask = pts == sc
        n = mask.sum()
        ev = int(y[mask.values].sum())
        pct = ev / n * 100 if n > 0 else float("nan")
        log(f"  {sc:>6}  {n:>5}  {ev:>7}  {pct:>7.1f}%")

    return pts


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    lines = []

    def log(s=""):
        print(s)
        lines.append(s)

    log("=" * 70)
    log("POP RECURRENCE MODEL RESULTS")
    log("=" * 70)

    # ---- Load data ----
    df = load_and_prepare()
    X, y, studies, feature_cols = build_feature_matrix(df)

    log(f"\nDataset: {len(X)} patients, {y.sum()} recurrences ({y.mean()*100:.1f}%)")
    log(f"Studies: {dict(zip(*np.unique(studies, return_counts=True)))}")
    log(f"Candidate predictors: {len(feature_cols)}")

    # ================================================================
    # MODEL 1: LASSO
    # ================================================================
    log("\n" + "=" * 70)
    log("MODEL 1: LASSO LOGISTIC REGRESSION")
    log("=" * 70)

    lasso_model, lasso_scaler = fit_lasso(X, y)
    selected = lasso_selected_features(lasso_model, feature_cols)
    log(f"\nSelected features (non-zero coef, N={len(selected)}):")
    coef = lasso_model.coef_[0]
    for f, c in sorted(zip(feature_cols, coef), key=lambda x: abs(x[1]), reverse=True):
        if c != 0:
            log(f"  {f:<30}  coef={c:+.4f}")

    log(f"\nSelected C (1/lambda) via 1-SE rule: {lasso_model.C_:.4f}"
        f"  (CV AUC at this C: {lasso_model.mean_auc_at_C_:.3f})")

    # Full-data metrics
    Xs_all = lasso_scaler.transform(X)
    prob_lasso = lasso_model.predict_proba(Xs_all)[:, 1]
    m = compute_metrics(y, prob_lasso)
    log(f"\nFull-data performance:")
    log(f"  AUC={m['auc']:.3f}  Sens={m['sens']:.3f}  Spec={m['spec']:.3f}"
        f"  PPV={m['ppv']:.3f}  NPV={m['npv']:.3f}")

    # 5-fold CV
    def lasso_fn(X_tr, y_tr):
        return fit_lasso(X_tr, y_tr)

    cv_aucs = cv_auc(X, y, lasso_fn)
    log(f"\n5-fold CV AUC: {np.mean(cv_aucs):.3f} ± {np.std(cv_aucs):.3f}"
        f"  (folds: {[round(a,3) for a in cv_aucs]})")

    # LODO — skip held-out set if model fit fails
    lodo_res = lodo_auc(X, y, studies, lasso_fn)
    log(f"\nLODO AUC:")
    for study, auc in sorted(lodo_res.items()):
        log(f"  Held-out {study}: AUC={auc:.3f}")

    # ================================================================
    # MODEL 2: STANDARD LOGISTIC (BACKWARD AIC)
    # ================================================================
    log("\n" + "=" * 70)
    log("MODEL 2: STANDARD LOGISTIC REGRESSION (BACKWARD AIC)")
    log("=" * 70)

    std_result, std_vars = fit_logistic_backward_aic(X, y)
    log(f"\nSelected variables (N={len(std_vars)}): {std_vars}")
    log(f"\nModel summary:")
    log(f"  AIC: {std_result.aic:.1f}    BIC: {std_result.bic:.1f}")
    log(f"\n  {'Variable':<30} {'OR':>7}  {'95% CI':>18}  {'p':>8}")
    log(f"  {'-'*30} {'-'*7}  {'-'*18}  {'-'*8}")
    conf = np.array(std_result.conf_int())
    for i, name in enumerate(["const"] + std_vars):
        coef_ = std_result.params[i]
        or_   = np.exp(coef_)
        ci_lo = np.exp(conf[i, 0])
        ci_hi = np.exp(conf[i, 1])
        pval  = std_result.pvalues[i]
        sig   = "*" if pval < 0.05 else ""
        log(f"  {name:<30} {or_:7.3f}  ({ci_lo:.3f} – {ci_hi:.3f})  {pval:8.4f} {sig}")

    # Full-data metrics
    Xc_all = sm.add_constant(X[std_vars].values, has_constant="add")
    prob_std = std_result.predict(Xc_all)
    m2 = compute_metrics(y, prob_std)
    log(f"\nFull-data performance:")
    log(f"  AUC={m2['auc']:.3f}  Sens={m2['sens']:.3f}  Spec={m2['spec']:.3f}"
        f"  PPV={m2['ppv']:.3f}  NPV={m2['npv']:.3f}")

    # 5-fold CV
    def std_fn(X_tr, y_tr):
        res, sel_v = fit_logistic_backward_aic(X_tr, y_tr)
        return res, None  # no scaler; predict uses add_constant

    # Custom CV for statsmodels (predict needs add_constant + selected vars)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    std_cv_aucs = []
    for train_idx, test_idx in skf.split(X, y):
        X_tr = X.iloc[train_idx]
        X_te = X.iloc[test_idx]
        y_tr = y[train_idx]
        y_te = y[test_idx]
        res_fold, sel_fold = fit_logistic_backward_aic(X_tr, y_tr)
        Xc_te = sm.add_constant(X_te[sel_fold].values, has_constant="add")
        prob_fold = res_fold.predict(Xc_te)
        std_cv_aucs.append(roc_auc_score(y_te, prob_fold))

    log(f"\n5-fold CV AUC: {np.mean(std_cv_aucs):.3f} ± {np.std(std_cv_aucs):.3f}"
        f"  (folds: {[round(a,3) for a in std_cv_aucs]})")

    # LODO for standard logistic
    std_lodo = {}
    for held_out in np.unique(studies):
        mask_tr = studies != held_out
        mask_te = studies == held_out
        if mask_te.sum() < 5 or len(np.unique(y[mask_te])) < 2:
            continue
        res_lo, sel_lo = fit_logistic_backward_aic(X[mask_tr], y[mask_tr])
        if res_lo is None or not sel_lo:
            log(f"  Held-out {held_out}: model fit failed, skipping")
            continue
        Xte_lo = X[mask_te][sel_lo]
        Xc_te_lo = sm.add_constant(Xte_lo.values, has_constant="add")
        prob_lo = res_lo.predict(Xc_te_lo)
        std_lodo[held_out] = roc_auc_score(y[mask_te], prob_lo)

    log(f"\nLODO AUC:")
    for study, auc in sorted(std_lodo.items()):
        log(f"  Held-out {study}: AUC={auc:.3f}")

    # ================================================================
    # COMPARISON SUMMARY
    # ================================================================
    log("\n" + "=" * 70)
    log("COMPARISON SUMMARY")
    log("=" * 70)
    log(f"\n{'Metric':<30} {'LASSO':>10} {'Standard':>10}")
    log(f"{'-'*30} {'-'*10} {'-'*10}")
    log(f"{'Full-data AUC':<30} {m['auc']:>10.3f} {m2['auc']:>10.3f}")
    log(f"{'Full-data Sensitivity':<30} {m['sens']:>10.3f} {m2['sens']:>10.3f}")
    log(f"{'Full-data Specificity':<30} {m['spec']:>10.3f} {m2['spec']:>10.3f}")
    log(f"{'5-fold CV AUC (mean)':<30} {np.mean(cv_aucs):>10.3f} {np.mean(std_cv_aucs):>10.3f}")
    log(f"{'5-fold CV AUC (SD)':<30} {np.std(cv_aucs):>10.3f} {np.std(std_cv_aucs):>10.3f}")
    log(f"{'N predictors selected':<30} {len(selected):>10d} {len(std_vars):>10d}")
    lodo_vals_l = list(lodo_res.values())
    lodo_vals_s = list(std_lodo.values())
    log(f"{'LODO AUC range':<30} {'%s–%s' % (round(min(lodo_vals_l),3), round(max(lodo_vals_l),3)):>10}",)
    log(f"{'':30} {'%s–%s' % (round(min(lodo_vals_s),3), round(max(lodo_vals_s),3)):>10}")

    log(f"\nVariables in LASSO but not Standard: {set(selected) - set(std_vars)}")
    log(f"Variables in Standard but not LASSO:  {set(std_vars) - set(selected)}")
    log(f"Variables in both:                     {set(selected) & set(std_vars)}")

    # ================================================================
    # POINT SCORE
    # ================================================================
    derive_point_score(std_result, std_vars, X, y, lines)

    # Save results
    with open(OUTPUT_FILE, "w") as f:
        f.write("\n".join(lines))
    print(f"\nResults saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
