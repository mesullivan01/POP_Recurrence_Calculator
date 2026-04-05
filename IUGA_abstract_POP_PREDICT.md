**Development of the POP-PREDICT Score: A Machine Learning-Derived Prediction Calculator for Recurrence Risk in Pelvic Organ Prolapse Surgery**

Sullivan, Marie; Kim, Shihyun; El Haraki, Amr

**Introduction:** There are several calculators commonly used in medicine such as the Vaginal Birth After Cesarean calculator, the Caprini Score, or the CHA₂DS₂-VASc score. These calculators are widely adopted because they integrate multiple clinical variables into a standardized score, improving risk stratification, enhancing shared decision-making, and optimizing patient outcomes.

**Objective:** To develop and validate a clinical risk score for prolapse recurrence following pelvic organ prolapse (POP) surgery incorporating patient characteristics and surgical approach.

**Methods:** We performed a pooled analysis of four prospective clinical trials (ALTIS, BEST, EPACT, SASS) including 752 women undergoing POP surgery between 2017-2024. Surgical approaches included sacrocolpopexy (N=472), native tissue repair with uterosacral/sacrospinous ligament suspension (N=232), and colpocleisis (N=48). A composite recurrence outcome was defined as POP-Q stage ≥2, any POP-Q point ≥0, or bothersome bulge symptoms at follow-up. LASSO logistic regression was used for predictor selection and model development, validated using 5-fold cross-validation and leave-one-dataset-out (LODO) external validation. Regression coefficients were converted to a point-based clinical risk score.

**Results:** Mean age was 63.6 years (SD 11.2), BMI 28.0 kg/m² (SD 5.6), and 56.3% presented with stage 3 prolapse. Composite recurrence occurred in 28.1% of patients. The model achieved AUC 0.65, sensitivity 0.58, specificity 0.72, PPV 0.41, and NPV 0.83. External validation confirmed consistent performance (LODO AUC range: 0.57-0.67). The POP-PREDICT score (0-14 points) incorporates eight predictors: surgery type (0-2 points), baseline Ba point (0-3), parity (0-2), height (0-2), baseline C point (0-2), hormonal status (0-1), baseline Aa point (0-1), and race (0-1). The score stratifies patients into low (0-4 points, ~10% recurrence), moderate (5-7 points, ~25%), high (8-10 points, ~40%), and very high risk (11-14 points, ~55%) categories.

**Conclusion:** The POP-PREDICT score is a clinical tool for preoperative risk stratification that incorporates surgical approach and recurrence risk. This score facilitates shared decision-making by quantifying expected recurrence risk based on patient characteristics and planned procedure.

**Table 1.** Patient Characteristics

| **Characteristic** | **Value** |
|---|---|
| Age, years | 63.6 (11.2) |
| BMI, kg/m² | 28.0 (5.6) |
| Parity, births | 2.6 (1.4) |
| Race | |
| &nbsp;&nbsp;&nbsp;&nbsp;White | 83.8% |
| &nbsp;&nbsp;&nbsp;&nbsp;Black | 7.9% |
| &nbsp;&nbsp;&nbsp;&nbsp;Hispanic | 5.7% |
| &nbsp;&nbsp;&nbsp;&nbsp;Other | 2.6% |
| Surgery Type | |
| &nbsp;&nbsp;&nbsp;&nbsp;Sacrocolpopexy | 62.8% |
| &nbsp;&nbsp;&nbsp;&nbsp;USLS/SSLF | 30.8% |
| &nbsp;&nbsp;&nbsp;&nbsp;Colpocleisis | 6.4% |
| Baseline POP-Q Stage | |
| &nbsp;&nbsp;&nbsp;&nbsp;Stage 2 | 32.2% |
| &nbsp;&nbsp;&nbsp;&nbsp;Stage 3 | 56.3% |
| &nbsp;&nbsp;&nbsp;&nbsp;Stage 4 | 11.5% |
| Composite recurrence | 28.1% |

*Values are presented as mean (SD) for continuous variables and % for categorical variables. USLS = uterosacral ligament suspension; SSLF = sacrospinous ligament fixation.*

**Table 2.** Predictive Model Performance

| **Outcome** | **AUC** | **Sensitivity** | **Specificity** | **PPV** | **NPV** |
|---|---|---|---|---|---|
| Composite recurrence | 0.65 | 0.58 | 0.72 | 0.41 | 0.83 |
| POP-Q Stage ≥2 | 0.63 | 0.61 | 0.65 | 0.38 | 0.82 |
| Any POP-Q point ≥0 | 0.68 | 0.54 | 0.75 | 0.31 | 0.89 |
| Bothersome bulge | 0.60 | 0.45 | 0.68 | 0.15 | 0.91 |

*PPV = positive predictive value; NPV = negative predictive value; AUC = area under the ROC curve.*

**POP-PREDICT SCORE v2.0**

*Prolapse Recurrence Risk Calculator*

| **Risk Factor** | **Criteria** | **Points** |
|---|---|---|
| **★ Surgery Type** | Colpocleisis | **0** |
| | Sacrocolpopexy | **1** |
| | USLS / SSLF | **2** |
| **Baseline Ba Point** | \< 0 cm | **0** |
| **(Anterior wall)** | 0 to 2 cm | **1** |
| | 3 to 4 cm | **2** |
| | \> 4 cm | **3** |
| **Parity** | 0-1 births | **0** |
| | 2-3 births | **1** |
| | ≥4 births | **2** |
| **Height** | \< 160 cm (\<5'3") | **0** |
| | 160-168 cm (5'3"-5'6") | **1** |
| | \> 168 cm (\>5'6") | **2** |
| **Baseline C Point** | \< -4 cm | **0** |
| **(Apical)** | -4 to 0 cm | **1** |
| | \> 0 cm | **2** |
| **Hormonal Status** | On HRT (any type) | **0** |
| | No HRT | **1** |
| **Baseline Aa Point** | ≤ 0 cm | **0** |
| | \> 0 cm | **1** |
| **Race** | Hispanic or Other | **0** |
| | White or Black | **1** |

**TOTAL SCORE: _____ / 14 points**

| | | |
|---|---|---|
| **0-4 points** | **LOW RISK** | ~10% recurrence probability |
| **5-7 points** | **MODERATE RISK** | ~25% recurrence probability |
| **8-10 points** | **HIGH RISK** | ~40% recurrence probability |
| **11-14 points** | **VERY HIGH RISK** | ~55% recurrence probability |

**Surgery Type Definitions:** Colpocleisis = obliterative procedure; Sacrocolpopexy = robotic, laparoscopic, or open mesh repair; USLS = uterosacral ligament suspension; SSLF = sacrospinous ligament fixation.

**Clinical Use:** This score supports preoperative counseling and shared decision-making. High-risk patients may benefit from mesh-augmented repair or enhanced postoperative surveillance.
