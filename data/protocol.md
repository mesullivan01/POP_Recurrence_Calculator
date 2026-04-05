**Development of a Prediction Calculator for Recurrence Risk in Pelvic Organ Prolapse Surgery**

Marie Sullivan, MD- Research Investigator

Amr El Haraki, MD- Principal Investigator

**Purpose and Rationale:** The purpose of this project is to develop a risk calculator for recurrence following surgical treatment for pelvic organ prolapse. There are several calculators commonly used in medicine such as the Vaginal Birth After Cesarean (VBAC) calculator for women desiring a trial of labor, the Caprini Score to evaluate postoperative risk of venous thromboembolism, or the CHA₂DS₂-VASc Score for estimating stroke risk in patients. These calculators are widely adopted because they integrate multiple clinical variables into a standardized score, improving risk stratification, enhancing shared decision-making, and optimizing patient outcomes. The calculator we will build will use pooled, de-identified, public-use datasets from multiple randomized controlled trials conducted by the Pelvic Floor Disorders Network (PFDN) and made available through the Eunice Kennedy Shriver National Institute of Child Health and Human Development (NICHD) Data and Specimen Hub (DASH).

The PFDN has conducted multiple multicenter randomized controlled trials, including:

- **OPTIMAL/eOPTIMAL** – Uterosacral ligament suspension vs sacrospinious ligament suspension for apical support loss

- **SUPeR/eSUPeR**– Vaginal hysterectomy with native tissue vault suspension vs. mesh hysteropexy suspension

- **Colpocleisis Trial** – Pelvic symptoms and patient satisfaction after colpocleisis

- **ASPIRe**- Apical Suspension Repair for Vaginal Vault Prolapse (sacrocolpopexy, transvaginal mesh, native tissue apical repair)

These datasets contain robust clinical, demographic, and surgical variables linked to postoperative outcomes. Developing a risk calculator using these high-quality datasets could improve preoperative counseling, shared decision-making, and patient satisfaction.

This retrospective study will also use data previously collected at Atrium Health Wake Forest Baptist Hospital such as our PACT, BEST, ALTIS, LOVE, SASS trials.

**Objectives**

- **Primary Objective:**\
  Develop a multivariable prediction model to estimate the probability of recurrence following different surgical procedures (mesh versus native tissue versus colpocleisis). The recurrence will be sorted out into re-operation, symptomatic and anatomic recurrence depending on available data. We will also estimate the probability of composite recurrence.

- **Secondary Objectives:**

- Identify demographic, surgical, and clinical factors most strongly associated with surgical success or failure.

- Create a user-friendly online calculator for clinician and patient use.

**Study Design**

**Type of Study:** Secondary analysis of existing, de-identified datasets either publicly available (PFDN) or institutionally based at Atrium Health facilities.\
**Design:** Retrospective cohort study pooling data from prior prolapse trials.\
**Population:** Participants enrolled in the above trials who met trial inclusion criteria and completed postoperative follow-up.\
**Timeframe:** Data from baseline through final follow-up in each trial.

**Data Sources**

Public-use, de-identified datasets will be accessed through NICHD DASH. The following trials will be included:

- **OPTIMAL** – NCT00597935

- **E-OPTIMAL** – NCT01204465

- **SUPeR** – NCT01802281

- **Colpocleisis Trial** – NCT00271297

- **ASPIRe** – NCT02676973

Local retrospective data previously collected at Atrium Health Wake Forest Baptist Hospital will also be utilized such as our PACT, BEST, ALTIS, LOVE, SASS trials.

**Variables of Interest**

- **Demographics:** Age, BMI, race/ethnicity, parity, comorbidities

- **Surgical Details:** Type of prolapse procedure, concurrent procedures, operative time, complications

- **Clinical Baseline Measures:** Pelvic Organ Prolapse Quantification (POP-Q) system, symptom severity scores

- **Outcomes:** Anatomic recurrence, symptomatic recurrence, reoperation rates

**Analysis Plan**

We will use a large language model (LLM)–assisted analytic workflow to develop and validate a recurrence risk calculator based on public-use repository.

**Data Preprocessing**

- Data will be downloaded in CSV or equivalent format and securely stored in accordance with institutional data security protocols.

- Variables relevant to recurrence (demographics, surgical approach, perioperative interventions, baseline pelvic floor function, comorbidities, operative details, and follow-up outcomes) will be standardized across studies.

- Missing values will be handled using multiple imputation or model-based approaches depending on variable type and extent of missingness.

- Variable definitions will follow original PFDN data dictionaries to ensure clinical consistency.

**Model Development with LLM**

- The LLM will be used to:

- Generate code for exploratory data analysis, survival analysis, and predictive modeling.

- Suggest candidate predictor variables and interaction terms based on both domain knowledge and dataset content.

- Produce and refine statistical model specifications.

- Interpret model outputs and produce explainable summaries for clinical audiences.

- All code and analytic steps generated by the LLM will be reviewed, validated, and executed by study investigators to ensure accuracy and reproducibility.

- The primary outcome will be recurrence of prolapse.

**Risk Calculator Construction**

- The final model will be converted into a user-friendly risk calculator (e.g., web-based tool or nomogram).

- The LLM will assist in:

- Generating the formula and variable mapping for implementation.

- Writing code for the interactive interface.

- Creating plain-language explanations of risk estimates for patients and providers.

- Calculator outputs will provide individualized recurrence probability estimates with 95% confidence intervals.

**Quality Control**

- Every analytic step proposed by the LLM will be verified by human investigators for:

- Correct statistical implementation.

- Clinical plausibility of predictors and coefficients.

- Avoidance of overfitting.

- All final results will be reproducible via documented, version-controlled code.

**LLM Limitations and Safeguards**

- **Non-autonomy:** The LLM will not directly access or process patient-level data independently. All prompts, outputs, and analyses will be conducted within secure institutional computing environments.

- **Human oversight:** All LLM-generated code, statistical methods, and interpretations will be reviewed and confirmed by investigators with expertise in urogynecology.

- **Error mitigation:** Any inconsistencies, statistical misapplications, or implausible findings generated by the LLM will be corrected before implementation.

- **Transparency:** All LLM prompts, responses, and resulting code will be archived in a project repository for reproducibility.

- **Bias assessment:** Model outputs will be examined for potential bias related to age, race, or other sociodemographic factors, and mitigation strategies will be documented if bias is detected.

**Risks to Subjects**

There is **no direct interaction with human subjects** and **no identifiable private information** will be used.\
Risk level: **Minimal** (analysis of de-identified public-use datasets).

**Potential Benefits**

- Development of a clinically useful risk calculator to inform preoperative counseling and patient decision-making.

- Contribution to surgical outcome prediction research in urogynecology.

**Privacy and Data Security**

- No identifiers will be present in the datasets; linkage to original identifiers is not possible.

**Funding**: None currently

**References**

- Eunice Kennedy Shriver National Institute of Child Health and Human Development (NICHD) DASH: [<u>https://dash.nichd.nih.gov/</u>](https://dash.nichd.nih.gov/)

- Pelvic Floor Disorders Network – Public Data Access: [<u>https://pelvicfloordisordersnetwork.org/AboutUs/PublicData</u>](https://pelvicfloordisordersnetwork.org/AboutUs/PublicData)
