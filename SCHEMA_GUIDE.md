# Schema Guide

This document explains every table and file in the mock dataset, what each field represents, and how the pieces connect across systems.

---

## The two hero claims

Everything revolves around two patients. **Margaret Sullivan (MBR001)** had a right knee replacement at Strong Memorial Hospital. **Robert Chen (MBR002)** was admitted for decompensated heart failure at Rochester General Hospital. Every table has rows for both, and the deliberate discrepancies are baked into their records specifically to make each challenge testable on day one.

---

## Facets (claims administration system)

Facets is the source of truth for what was billed and paid. Five tables, all joined on `claim_id` or `member_id`.

### `facets_claim_header`
One row per claim. The core record.

| Field | Description |
|---|---|
| `claim_id` | Primary key. Hero claims are `CLM2024-H001` and `CLM2024-H002`. |
| `member_id` / `subscriber_id` | Patient and subscriber identifiers. |
| `provider_id` / `provider_name` | Rendering provider NPI and name. |
| `claim_type` | `UB04` (institutional/inpatient) or `CMS1500` (professional/physician). |
| `total_billed_amount` | What the provider charged. |
| `total_allowed_amount` | What the plan agreed to pay (contracted rate). |
| `drg_code` / `drg_days` | MS-DRG grouping code and authorized length of stay. UB04 only. |
| `service_from_date` / `service_to_date` | Statement period (FL 6 on UB-04). |
| `discharge_status` | UB-04 FL17 code — how the patient left (home, SNF, expired, etc.). |
| `primary_diagnosis` / `secondary_diagnoses` | ICD-10 codes. Secondary codes are pipe-delimited. |
| `micro_image_id` | FK to `quick_claim_manifest`. Non-null means a paper claim image exists in the Volume. |
| `claim_status` | `paid`, `adjusted`, or `denied`. |

### `facets_auth_summary`
One row per claim that required prior authorization. Not all claims need auth — only high-dollar inpatient UB04s.

| Field | Description |
|---|---|
| `claim_id` | FK to `facets_claim_header`. |
| `auth_ref_number` | Authorization reference number. FK to `care_advance_authorizations`. |
| `auth_status` | `approved`, `pending`, or `denied`. |
| `auth_from_date` / `auth_to_date` | The dates the authorization covers. |
| `authorized_days` | Number of inpatient days approved. |
| `authorized_amount` | Dollar amount approved. |
| `requesting_provider_npi` | The NPI on the authorization request. |

**Sullivan's discrepancy:** `authorized_days = 3`, actual `drg_days = 4`. `authorized_amount = $36,500` vs. `total_allowed_amount = $52,200`.

### `facets_benefit_summary`
One row per member. Their plan-level cost-sharing rules for the plan year.

| Field | Description |
|---|---|
| `member_id` | FK to all other Facets tables. |
| `plan_id` | Plan name (e.g., `PPO-GOLD`, `HMO-SILVER`). |
| `oop_max_individual` / `oop_max_family` | The cap on annual out-of-pocket spending. Both hero members have a $5,000 individual max. |
| `deductible_individual` / `deductible_family` | Annual deductible before cost-sharing kicks in. |
| `copay_amount` / `coinsurance_pct` | Per-visit copay and coinsurance rate. |

### `facets_accumulators`
Two rows per member (one `OOP`, one `deductible`) tracking year-to-date spending toward each limit.

| Field | Description |
|---|---|
| `accumulator_type` | `OOP` or `deductible`. |
| `accumulated_amount` | How much the member has accumulated toward this limit. |
| `family_accumulated_amount` | Same, at the family level. |
| `service_effective_date` | Date of the most recent claim contributing to this accumulator. |

**Chen's discrepancy:** `accumulated_amount = $5,420` — $420 *over* his $5,000 OOP max, meaning he was overpaid at some point and the plan needs to recover or correct it.

### `facets_claim_history`
Prior claims in the 90-day lookback window for each member. Used in Challenge 5 to reconstruct the running OOP total.

> **Important:** The 90-day window uses `service_from_date`, not `paid_date` or `processed_date`. This is the regulatory requirement and a common source of bugs.

---

## Care Advance (prior authorization system)

### `care_advance_authorizations`
One record per authorization, shaped like a REST API response. In production, Challenge 4's LangGraph agent calls this endpoint live rather than reading from a pre-replicated table.

| Field | Description |
|---|---|
| `auth_ref_number` | FK to `facets_auth_summary.auth_ref_number`. |
| `requesting_provider_npi` | Provider who submitted the auth request. |
| `rendering_provider_npi` | Provider who actually rendered the service. |
| `diagnosis_codes` / `procedure_codes` | Array fields — what was authorized. |
| `authorized_days` / `auth_from_date` / `auth_to_date` | Authorization scope. |
| `decision_support_reviewed` | Whether clinical decision support was consulted before approval. |

**Sullivan's discrepancy:** `rendering_provider_npi` in Care Advance (`9876543210`) differs from `requesting_provider_npi` in Facets (`1234567890`). This is the second discrepancy the Challenge 4 agent needs to surface alongside the date/amount mismatch.

**Chen's record:** Clean — all fields match Facets exactly.

---

## Cognos (IBM BI / accumulator report)

### `cognos_accumulator_report`
One row per member per benefit type. Sourced from a nightly Excel export out of Cognos. Represents what the BI reporting layer *thinks* the accumulators are — which may lag Facets by up to 24 hours.

| Field | Description |
|---|---|
| `subscriber_id` / `member_id` | Member identifiers. |
| `benefit_type` | `OOP` or `deductible`. |
| `accumulated_amount` | Cognos's view of the accumulated balance. |
| `claim_count` | Number of claims contributing to this balance. |
| `last_claim_date` | Most recent claim date in the Cognos extract. |

**Chen's discrepancy:** `accumulated_amount = $4,750` in Cognos vs. `$5,420` in Facets — a $670 gap. The policy doc (`POL-BEN-2024-015`) explains the common causes (reversed claims, COB adjustments hitting Facets before the nightly refresh).

**Sullivan's record:** Matches Facets exactly — no discrepancy.

---

## CMS public reference data

Three tables loaded from annual CMS releases. Load once; refresh every October 1.

### `cms_icd10_hierarchy`
Diagnosis code reference. Maps ICD-10 codes to human-readable descriptions, clinical categories, and chapters.

| Field | Description |
|---|---|
| `icd10_code` | Primary key (e.g., `I50.9`). |
| `code_description` | Full clinical description. |
| `category_code` / `category_description` | Parent category grouping. |
| `chapter` | Broad disease chapter (e.g., "Diseases of the circulatory system"). |
| `is_billable` | Whether this code can be used as a principal diagnosis on a claim. |

### `cms_hcc_mappings`
Maps ICD-10 codes to HCC (Hierarchical Condition Category) risk scores. HCC scores drive risk adjustment — they determine how much the plan receives from CMS to cover a member's expected cost.

| Field | Description |
|---|---|
| `hcc_category` | HCC category number. `0` means no HCC mapping. |
| `hcc_description` | Clinical grouping name (e.g., "Congestive Heart Failure"). |
| `raf_weight` | Risk Adjustment Factor — how much this condition increases expected cost. |

Chen's admission has three HCC-mapped diagnoses: CHF (0.331), CKD Stage 5 (0.289), DM with complications (0.302). The policy doc calls out that these must be accurately coded on the claim for correct risk adjustment.

### `cms_ccs_categories`
Maps ICD-10 codes to AHRQ Clinical Classifications Software (CCS) categories — broader groupings useful for population-level analysis and grouping "all heart failure codes" into a single bucket.

| Field | Description |
|---|---|
| `ccs_category` | Numeric category (e.g., `108` = congestive heart failure). |
| `ccs_label` | Human-readable category name. |
| `is_chronic` | Whether this condition is classified as chronic. |

---

## Quick Claim / paper claims

### `quick_claim_manifest`
The intake log for paper claim images. One row per image file.

| Field | Description |
|---|---|
| `image_id` | FK to `facets_claim_header.micro_image_id`. |
| `claim_id` | FK to `facets_claim_header.claim_id`. |
| `form_type` | `UB04` or `CMS1500` — determined before OCR via `ai_classify`. |
| `file_path` | Live path in the UC Volume (rewritten by setup notebook from the repo-relative path). |
| `file_format` | `PDF`, `TIFF`, or `JPG`. |

The two hero claims have real PDFs: `IMG00001.pdf` (Sullivan's UB-04) and `IMG00002.pdf` (Chen's UB-04). Challenge 1 reads these via `READ_FILES`, runs `ai_parse_document` + `ai_classify` + `ai_extract`, then compares extracted fields back to `facets_claim_header`.

---

## Policy documents (SharePoint PDFs)

No table — these are files in `/Volumes/.../policy_docs/`, indexed into a Vector Search index for Challenge 3.

| File | Contents |
|---|---|
| `POL-ORTHO-2024-001_knee_replacement_prior_auth.pdf` | Prior auth requirements for elective knee replacement. Explicitly states 3-day expected LOS and lists audit triggers for LOS overruns and NPI mismatches — Sullivan's claim hits both. |
| `POL-CARD-2024-008_heart_failure_admission_criteria.pdf` | Medical necessity criteria for CHF inpatient admission. Covers which secondary diagnoses qualify as MCCs for DRG 291, and HCC coding requirements for risk adjustment. |
| `POL-BEN-2024-015_oop_accumulator_policy.pdf` | OOP max accumulator policy. Defines the 90-day lookback rule, explains Facets vs. Cognos lag scenarios, and explicitly prohibits automated write-back without human approval. |

The content is written so that querying "knee replacement authorization days" or "OOP max discrepancy" retrieves the right document and directly answers the auditor's question.

---

## How it all connects

```
quick_claim_manifest ──► PDF in UC Volume ──► ai_parse_document ──► ai_extract
                                                                          │
                                                                          ▼
facets_claim_header ◄──────────────────────────── field comparison (Challenge 1)
        │
        ├── facets_auth_summary ◄──► care_advance_authorizations   (Challenge 4)
        │
        ├── facets_benefit_summary
        │         +                                                 (Challenge 5)
        ├── facets_accumulators ◄──► cognos_accumulator_report
        │         +
        └── facets_claim_history

cms_icd10_hierarchy  ┐
cms_hcc_mappings     ├── code groupings lookup                     (Challenge 3)
cms_ccs_categories   ┘
        +
policy_docs PDFs ──► Vector Search index ──► AI Agent
```

The primary join key everywhere is `claim_id` → `member_id`. One claim, one member, one authorization, one accumulator record — that's the grain. The discrepancies sit at the seams between systems, which is exactly what the audit pipeline is built to find.

---

## Baked-in discrepancies

| Claim | System A | System B | Discrepancy | Challenge |
|---|---|---|---|---|
| CLM2024-H001 (Sullivan) | `facets_claim_header`: `drg_days = 4` | `facets_auth_summary`: `authorized_days = 3` | 1-day LOS overrun | 4 |
| CLM2024-H001 (Sullivan) | `facets_auth_summary`: `authorized_amount = $36,500` | `facets_claim_header`: `total_allowed_amount = $52,200` | $15,700 underpaid (30%) | 4 |
| CLM2024-H001 (Sullivan) | `facets_auth_summary`: NPI `1234567890` | `care_advance_authorizations`: rendering NPI `9876543210` | Provider NPI mismatch | 4 |
| CLM2024-H002 (Chen) | `facets_accumulators`: OOP `$5,420` | `cognos_accumulator_report`: OOP `$4,750` | $670 gap; member $420 over OOP max | 5 |
