# Databricks notebook source
# MAGIC %md
# MAGIC # Claims Audit Hackathon — Mock Data Setup
# MAGIC
# MAGIC **Run this notebook once** to:
# MAGIC 1. Create Unity Catalog schema and Volumes
# MAGIC 2. Upload PDF files (UB-04 claims + SharePoint policy docs) into Volumes
# MAGIC 3. Create and load all Delta tables
# MAGIC 4. Run sanity-check joins
# MAGIC
# MAGIC ### Before you start
# MAGIC 1. Attach to a cluster (DBR 14.3 LTS or later, Unity Catalog enabled)
# MAGIC 2. Set `CATALOG` and `SCHEMA` below — both will be created if they don't exist
# MAGIC 3. Run All (~1 minute)

# COMMAND ----------

# ── Configuration ─────────────────────────────────────────────────────────────
CATALOG = "dev"             # ← change to your catalog
SCHEMA  = "claims_hack"  # ← will be created if it doesn't exist

# COMMAND ----------

# MAGIC %md ## 0 — Resolve repo root

# COMMAND ----------

import os

# When running from Databricks Repos the notebook path is something like
# /Workspace/Repos/<user>/claims-hackathon-mock-data/setup/load_mock_data
# We walk up two levels to get the repo root.
try:
    nb_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
    REPO_ROOT = "/Workspace" + "/".join(nb_path.replace("/Workspace", "").split("/")[:-2])
except Exception:
    REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in dir() else "."

print(f"Repo root: {REPO_ROOT}")

SEED     = f"{REPO_ROOT}/seed_data"
VOL_BASE = f"/Volumes/{CATALOG}/{SCHEMA}"

# COMMAND ----------

# MAGIC %md ## 1 — Create catalog, schema, and Volumes

# COMMAND ----------

spark.sql(f"CREATE CATALOG IF NOT EXISTS `{CATALOG}`")
spark.sql(f"USE CATALOG `{CATALOG}`")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{SCHEMA}`")
spark.sql(f"USE SCHEMA `{SCHEMA}`")

spark.sql(f"CREATE VOLUME IF NOT EXISTS `{CATALOG}`.`{SCHEMA}`.claims_inbound")
spark.sql(f"CREATE VOLUME IF NOT EXISTS `{CATALOG}`.`{SCHEMA}`.policy_docs")

print(f"Ready: {CATALOG}.{SCHEMA}")
print(f"  Volume: {VOL_BASE}/claims_inbound")
print(f"  Volume: {VOL_BASE}/policy_docs")

# COMMAND ----------

# MAGIC %md ## 2 — Upload PDF files into Volumes

# COMMAND ----------

import shutil, glob

def upload_dir(src_glob: str, dest_volume: str):
    files = sorted(glob.glob(src_glob))
    if not files:
        print(f"  WARNING: no files matched {src_glob}")
        return
    for src in files:
        fname = os.path.basename(src)
        dest = f"{dest_volume}/{fname}"
        shutil.copy2(src, dest)
        size_kb = os.path.getsize(dest) // 1024
        print(f"  {fname} -> {dest}  ({size_kb} KB)")

print("Uploading UB-04 paper claim images...")
upload_dir(f"{SEED}/quick_claim/images/*.pdf", f"{VOL_BASE}/claims_inbound")

print("\nUploading SharePoint policy documents...")
upload_dir(f"{SEED}/sharepoint/docs/*.pdf", f"{VOL_BASE}/policy_docs")

# COMMAND ----------

# MAGIC %md ## 3 — Helper: load seed files into Delta tables

# COMMAND ----------

def load_csv(table: str, rel_path: str):
    path = f"{SEED}/{rel_path}"
    df = spark.read.option("header", True).option("inferSchema", True).csv(f"file:{path}")
    df.write.format("delta").mode("overwrite").saveAsTable(f"`{CATALOG}`.`{SCHEMA}`.`{table}`")
    n = spark.table(f"`{CATALOG}`.`{SCHEMA}`.`{table}`").count()
    print(f"  {table}: {n} rows")

def load_json(table: str, rel_path: str):
    path = f"{SEED}/{rel_path}"
    df = spark.read.option("multiline", True).json(f"file:{path}")
    drop_cols = [c for c in df.columns if c.startswith("_")]
    if drop_cols:
        df = df.drop(*drop_cols)
    df.write.format("delta").mode("overwrite").saveAsTable(f"`{CATALOG}`.`{SCHEMA}`.`{table}`")
    n = spark.table(f"`{CATALOG}`.`{SCHEMA}`.`{table}`").count()
    print(f"  {table}: {n} rows")

# COMMAND ----------

# MAGIC %md ## 4 — Load Facets tables

# COMMAND ----------

print("Loading Facets tables...")
load_csv("facets_claim_header",    "facets/claim_header.csv")
load_csv("facets_auth_summary",    "facets/auth_summary.csv")
load_csv("facets_benefit_summary", "facets/benefit_summary.csv")
load_csv("facets_accumulators",    "facets/accumulators.csv")
load_csv("facets_claim_history",   "facets/claim_history.csv")

# COMMAND ----------

# MAGIC %md ## 5 — Load Care Advance authorizations

# COMMAND ----------

print("Loading Care Advance...")
load_json("care_advance_authorizations", "care_advance/authorizations.json")

# COMMAND ----------

# MAGIC %md ## 6 — Load Cognos accumulator report

# COMMAND ----------

print("Loading Cognos...")
load_csv("cognos_accumulator_report", "cognos/accumulator_report.csv")

# COMMAND ----------

# MAGIC %md ## 7 — Load CMS public reference data

# COMMAND ----------

print("Loading CMS reference tables...")
load_csv("cms_icd10_hierarchy", "cms_public/icd10_hierarchy.csv")
load_csv("cms_hcc_mappings",    "cms_public/hcc_mappings.csv")
load_csv("cms_ccs_categories",  "cms_public/ccs_categories.csv")

# COMMAND ----------

# MAGIC %md ## 8 — Load Quick Claim manifest with live Volume paths

# COMMAND ----------

print("Loading Quick Claim manifest...")
load_csv("_quick_claim_manifest_raw", "quick_claim/paper_claim_manifest.csv")

# Rewrite file_path to point at the actual Volume location
spark.sql(f"""
  CREATE OR REPLACE TABLE `{CATALOG}`.`{SCHEMA}`.`quick_claim_manifest` AS
  SELECT
    image_id,
    claim_id,
    member_id,
    form_type,
    CONCAT('{VOL_BASE}/claims_inbound/', image_id, '.pdf') AS file_path,
    file_format,
    received_date
  FROM `{CATALOG}`.`{SCHEMA}`.`_quick_claim_manifest_raw`
""")
spark.sql(f"DROP TABLE `{CATALOG}`.`{SCHEMA}`.`_quick_claim_manifest_raw`")

n = spark.table(f"`{CATALOG}`.`{SCHEMA}`.`quick_claim_manifest`").count()
print(f"  quick_claim_manifest: {n} rows  (paths -> {VOL_BASE}/claims_inbound/)")

# COMMAND ----------

# MAGIC %md ## 9 — Verify: files in Volumes

# COMMAND ----------

print("=== claims_inbound ===")
display(dbutils.fs.ls(f"{VOL_BASE}/claims_inbound"))

print("\n=== policy_docs ===")
display(dbutils.fs.ls(f"{VOL_BASE}/policy_docs"))

# COMMAND ----------

# MAGIC %md ## 10 — Row counts

# COMMAND ----------

tables = [
    "facets_claim_header", "facets_auth_summary", "facets_benefit_summary",
    "facets_accumulators", "facets_claim_history",
    "care_advance_authorizations",
    "cognos_accumulator_report",
    "cms_icd10_hierarchy", "cms_hcc_mappings", "cms_ccs_categories",
    "quick_claim_manifest",
]
print(f"\n{'Table':<35} {'Rows':>6}")
print("-" * 43)
for t in tables:
    try:
        n = spark.table(f"`{CATALOG}`.`{SCHEMA}`.`{t}`").count()
        print(f"{t:<35} {n:>6}")
    except Exception as e:
        print(f"{t:<35}  ERROR: {e}")

# COMMAND ----------

# MAGIC %md ## 11 — Sanity checks: baked-in discrepancies

# COMMAND ----------

# Challenge 4: auth vs claim discrepancies — hero claim H001
print("Challenge 4 - Auth vs Claim discrepancies:")
display(spark.sql(f"""
  SELECT
    h.claim_id,
    h.member_id,
    h.drg_days                                          AS actual_los,
    a.authorized_days                                   AS auth_days,
    h.drg_days - a.authorized_days                      AS los_overrun,
    h.total_allowed_amount                              AS facets_allowed,
    a.authorized_amount                                 AS auth_amount,
    ROUND((h.total_allowed_amount - a.authorized_amount)
          / h.total_allowed_amount * 100, 1)            AS pct_underpaid,
    ca.rendering_provider_npi                           AS ca_rendering_npi,
    a.requesting_provider_npi                           AS facets_npi,
    ca.rendering_provider_npi
      != a.requesting_provider_npi                      AS npi_mismatch
  FROM `{CATALOG}`.`{SCHEMA}`.facets_claim_header            h
  JOIN `{CATALOG}`.`{SCHEMA}`.facets_auth_summary            a  USING (claim_id)
  JOIN `{CATALOG}`.`{SCHEMA}`.care_advance_authorizations    ca
       ON a.auth_ref_number = ca.auth_ref_number
  WHERE h.drg_days > a.authorized_days
     OR h.total_allowed_amount > a.authorized_amount * 1.10
     OR ca.rendering_provider_npi != a.requesting_provider_npi
  ORDER BY h.claim_id
"""))

# COMMAND ----------

# Challenge 5: Cognos vs Facets OOP discrepancy — hero claim H002
print("Challenge 5 - Cognos vs Facets OOP discrepancies:")
display(spark.sql(f"""
  SELECT
    f.member_id,
    b.oop_max_individual,
    f.accumulated_amount                                    AS facets_oop,
    c.accumulated_amount                                    AS cognos_oop,
    ROUND(f.accumulated_amount - c.accumulated_amount, 2)  AS delta,
    ROUND(f.accumulated_amount - b.oop_max_individual, 2)  AS over_max_by,
    CASE WHEN f.accumulated_amount > b.oop_max_individual
         THEN 'OVER MAX' ELSE 'within max' END              AS oop_status
  FROM `{CATALOG}`.`{SCHEMA}`.facets_accumulators            f
  JOIN `{CATALOG}`.`{SCHEMA}`.facets_benefit_summary         b USING (member_id)
  JOIN `{CATALOG}`.`{SCHEMA}`.cognos_accumulator_report      c USING (member_id)
  WHERE f.accumulator_type = 'OOP'
    AND c.benefit_type = 'OOP'
    AND ABS(f.accumulated_amount - c.accumulated_amount) > 50
  ORDER BY delta DESC
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup complete
# MAGIC
# MAGIC | Resource | Location |
# MAGIC |---|---|
# MAGIC | Delta tables | `CATALOG.SCHEMA.*` |
# MAGIC | UB-04 claim PDFs | `/Volumes/CATALOG/SCHEMA/claims_inbound/` |
# MAGIC | Policy doc PDFs | `/Volumes/CATALOG/SCHEMA/policy_docs/` |
# MAGIC | Manifest (live paths) | `CATALOG.SCHEMA.quick_claim_manifest` |
# MAGIC
# MAGIC **Baked-in discrepancies:**
# MAGIC - **CLM2024-H001** (Sullivan): 4-day LOS vs 3-day auth, $15.7K underpaid, rendering NPI mismatch -> Challenge 4
# MAGIC - **CLM2024-H002** (Chen): Facets OOP $5,420 vs Cognos $4,750 ($670 gap, $420 over OOP max) -> Challenge 5
