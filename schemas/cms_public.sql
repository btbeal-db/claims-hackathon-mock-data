-- CMS Public Reference Data
-- Source: CMS ICD-10-CM FY release (Oct 1 annually), CMS-HCC Risk Adjustment Model, AHRQ CCSR
-- Load once; refresh annually

CREATE TABLE IF NOT EXISTS {catalog}.{schema}.cms_icd10_hierarchy (
    icd10_code              STRING NOT NULL,
    code_description        STRING,
    category_code           STRING,
    category_description    STRING,
    chapter                 STRING,
    is_billable             BOOLEAN,
    effective_date          DATE,
    expiration_date         DATE
) USING DELTA;

CREATE TABLE IF NOT EXISTS {catalog}.{schema}.cms_hcc_mappings (
    icd10_code      STRING NOT NULL,
    hcc_category    INT,                  -- 0 = no HCC mapping
    hcc_description STRING,
    raf_weight      DOUBLE,               -- Risk Adjustment Factor
    model_year      INT
) USING DELTA;

CREATE TABLE IF NOT EXISTS {catalog}.{schema}.cms_ccs_categories (
    icd10_code      STRING NOT NULL,
    ccs_category    INT,
    ccs_label       STRING,
    is_chronic      BOOLEAN
) USING DELTA;
