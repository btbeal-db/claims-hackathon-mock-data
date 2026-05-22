-- Facets Claims Administration System
-- All tables live in the bronze layer; replicated via CDC or manual seed

CREATE TABLE IF NOT EXISTS {catalog}.{schema}.facets_claim_header (
    claim_id            STRING        NOT NULL,
    member_id           STRING        NOT NULL,
    subscriber_id       STRING,
    provider_id         STRING,           -- NPI
    provider_name       STRING,
    claim_type          STRING,           -- UB04 | CMS1500
    total_billed_amount DOUBLE,
    total_allowed_amount DOUBLE,
    drg_code            STRING,           -- blank for CMS-1500
    drg_days            INT,
    service_from_date   DATE,
    service_to_date     DATE,
    discharge_status    STRING,           -- UB-04 FL17 code; blank for CMS-1500
    primary_diagnosis   STRING,           -- ICD-10 code
    secondary_diagnoses STRING,           -- pipe-delimited ICD-10 codes
    micro_image_id      STRING,           -- FK to paper claim image; NULL if no image
    processed_date      DATE,
    claim_status        STRING            -- paid | adjusted | denied
) USING DELTA TBLPROPERTIES ("delta.enableChangeDataFeed" = "true");

CREATE TABLE IF NOT EXISTS {catalog}.{schema}.facets_auth_summary (
    claim_id                STRING NOT NULL,
    auth_ref_number         STRING,
    member_id               STRING,
    auth_status             STRING,       -- approved | pending | denied
    auth_from_date          DATE,
    auth_to_date            DATE,
    authorized_days         INT,
    authorized_amount       DOUBLE,
    requesting_provider_npi STRING,
    decision_support_reviewed BOOLEAN
) USING DELTA;

CREATE TABLE IF NOT EXISTS {catalog}.{schema}.facets_benefit_summary (
    member_id               STRING NOT NULL,
    plan_id                 STRING,
    plan_year               INT,
    copay_amount            DOUBLE,
    coinsurance_pct         DOUBLE,
    oop_max_individual      DOUBLE,
    oop_max_family          DOUBLE,
    deductible_individual   DOUBLE,
    deductible_family       DOUBLE,
    benefit_effective_date  DATE
) USING DELTA;

CREATE TABLE IF NOT EXISTS {catalog}.{schema}.facets_accumulators (
    member_id               STRING NOT NULL,
    subscriber_id           STRING,
    plan_id                 STRING,
    plan_year               INT,
    accumulator_type        STRING,       -- OOP | deductible
    service_effective_date  DATE,
    accumulated_amount      DOUBLE,
    family_accumulated_amount DOUBLE,
    last_updated_ts         TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS {catalog}.{schema}.facets_claim_history (
    member_id           STRING NOT NULL,
    subscriber_id       STRING,
    claim_id            STRING,
    service_from_date   DATE,
    service_to_date     DATE,
    claim_type          STRING,
    allowed_amount      DOUBLE,
    paid_amount         DOUBLE,
    provider_id         STRING
) USING DELTA;
