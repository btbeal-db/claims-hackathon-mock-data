-- Cognos IBM BI — Accumulator Report
-- Sourced from Excel export; deliberate discrepancies vs. facets_accumulators baked into seed data

CREATE TABLE IF NOT EXISTS {catalog}.{schema}.cognos_accumulator_report (
    subscriber_id           STRING NOT NULL,
    member_id               STRING,
    member_name             STRING,
    plan_id                 STRING,
    plan_year               INT,
    benefit_type            STRING,       -- OOP | deductible
    service_effective_date  DATE,
    accumulated_amount      DOUBLE,
    family_accumulated_amount DOUBLE,
    claim_count             INT,
    last_claim_date         DATE
) USING DELTA;
