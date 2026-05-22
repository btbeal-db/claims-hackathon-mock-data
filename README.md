# Claims Audit Hackathon — Mock Data

Mock seed data for all four claims audit pipeline challenges. Internally consistent across systems:
same `member_id` / `claim_id` appear in Facets, Care Advance, and Cognos. Deliberate discrepancies
are baked in for challenge testing.

## Quick start

1. Add this repo to **Databricks Repos** (Workspace → Repos → Add Repo)
2. Open `setup/load_mock_data.py` as a notebook
3. Set `CATALOG` and `SCHEMA` at the top of the notebook
4. **Run All**

All tables will be created and loaded in under a minute.

---

## What's in the data

| Challenge | Tables Used |
|-----------|-------------|
| 1 — OCR & Validation | `facets_claim_header`, `quick_claim_manifest` |
| 3 — Policy Lookup Agent | `facets_claim_header`, `cms_icd10_hierarchy`, `cms_hcc_mappings`, `cms_ccs_categories` |
| 4 — Pre-Auth Verification | `facets_claim_header`, `facets_auth_summary`, `care_advance_authorizations` |
| 5 — Accumulator Audit | `facets_accumulators`, `facets_benefit_summary`, `facets_claim_history`, `cognos_accumulator_report` |

## Baked-in discrepancies

The seed data includes deliberate mismatches to make each challenge testable on day one:

- **~3 auth records** in `care_advance_authorizations` have date shifts or provider NPI mismatches
  vs. `facets_auth_summary` → triggers Challenge 4 mismatch path
- **~3 members** in `cognos_accumulator_report` have OOP amounts that differ from
  `facets_accumulators` by 5–20% → triggers Challenge 5 discrepancy flag

## Repo structure

```
seed_data/
  facets/             claim_header, auth_summary, benefit_summary, accumulators, claim_history
  care_advance/       authorizations.json  (REST API response shape)
  cognos/             accumulator_report.csv  (Excel export shape)
  cms_public/         icd10_hierarchy, hcc_mappings, ccs_categories
  quick_claim/        paper_claim_manifest.csv  (image file manifest)
schemas/
  facets.sql          DDL for all Facets tables
  care_advance.sql    DDL for authorization table
  cognos.sql          DDL for accumulator report
  cms_public.sql      DDL for ICD-10, HCC, CCS tables
  quick_claim.sql     DDL for paper claim manifest
setup/
  load_mock_data.py   Databricks notebook — run this
```

## Members & scenarios

10 synthetic members (MBR001–MBR010). OOP scenarios:
- **Near OOP max** (~3 members): tests the over-threshold alert path
- **Over OOP max** (~1–2 members): tests the write-back correction path
- **Under** (~5 members): baseline

## Notes

- No real PHI. All data is synthetic.
- `quick_claim_manifest` references S3 paths that don't exist — the manifest is the fixture.
  On hackathon day, replace with real UC Volume paths if actual images are available.
- CMS reference data (ICD-10, HCC, CCS) is a curated 30-row subset of common codes.
  Production load would be the full annual CMS release files.
