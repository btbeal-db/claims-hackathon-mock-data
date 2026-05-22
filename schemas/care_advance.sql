-- Care Advance Prior Authorization System
-- Populated from REST API response; seeded from JSON for hackathon

CREATE TABLE IF NOT EXISTS {catalog}.{schema}.care_advance_authorizations (
    auth_ref_number             STRING NOT NULL,
    member_id                   STRING,
    requesting_provider_npi     STRING,
    rendering_provider_npi      STRING,
    provider_name               STRING,
    diagnosis_codes             ARRAY<STRING>,
    procedure_codes             ARRAY<STRING>,
    service_codes               ARRAY<STRING>,
    auth_from_date              DATE,
    auth_to_date                DATE,
    authorized_days             INT,
    services_rendered           STRING,
    approval_status             STRING,       -- approved | pending | denied
    decision_support_reviewed   BOOLEAN,
    decision_date               DATE
) USING DELTA;
