-- first try: read_json_auto
-- it failed with "JSON transform error": the records don't all have the same fields
-- CREATE OR REPLACE TABLE raw_locations AS
-- SELECT *
-- FROM read_json_auto('data/raw/*.json');

-- raw layer: one row per location, the whole record kept as one JSON value
CREATE OR REPLACE TABLE raw_locations AS
SELECT
    filename,
    content::JSON AS data
FROM read_text('data/raw/*.json');
