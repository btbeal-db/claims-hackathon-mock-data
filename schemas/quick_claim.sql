-- Quick Claim / Smart Data Solutions — Paper Claims Manifest
-- Actual binary image files (PDF/TIFF/JPG) are referenced by file_path in the UC Volume.
-- This table is the intake manifest; the actual files are loaded via READ_FILES / Auto Loader.

CREATE TABLE IF NOT EXISTS {catalog}.{schema}.quick_claim_manifest (
    image_id        STRING NOT NULL,      -- FK to facets_claim_header.micro_image_id
    claim_id        STRING,
    member_id       STRING,
    form_type       STRING,               -- UB04 | CMS1500
    file_path       STRING,               -- UC Volume path or S3 URI
    file_format     STRING,               -- PDF | TIFF | JPG
    received_date   DATE
) USING DELTA;
