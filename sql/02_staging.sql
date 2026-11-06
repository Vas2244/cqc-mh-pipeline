-- staging: one row per currently registered service, with the fields I need
CREATE OR REPLACE TABLE stg_locations AS
SELECT
    data->>'locationId'      AS location_id,
    data->>'name'            AS name,
    data->>'providerId'      AS provider_id,
    data->>'localAuthority'  AS borough,
    -- shorten the ICB name: "NHS North East London Integrated Care Board" -> "North East London"
    replace(replace(data->>'onspdIcbName', 'NHS ', ''), ' Integrated Care Board', '') AS icb,
    CASE
        WHEN data->>'type' = 'NHS Healthcare Organisation' THEN 'NHS'
        WHEN data->>'type' = 'Independent Healthcare Org' THEN 'Independent'
        ELSE 'Other'
    END AS run_by,
    TRY_CAST(data->>'onspdLatitude' AS DOUBLE)  AS latitude,
    TRY_CAST(data->>'onspdLongitude' AS DOUBLE) AS longitude
FROM raw_locations
-- most of what the API returned had closed (158 registered, 301 deregistered), so keep current ones only
WHERE data->>'registrationStatus' = 'Registered';

-- one row per service and service type (a service can have several)
CREATE OR REPLACE TABLE stg_service_types AS
SELECT
    data->>'locationId' AS location_id,
    unnest(data->>'$.gacServiceTypes[*].name') AS service_type
FROM raw_locations
WHERE data->>'registrationStatus' = 'Registered';

-- one row per service and specialism (who it's for like eating disorders, children)
CREATE OR REPLACE TABLE stg_specialisms AS
SELECT
    data->>'locationId' AS location_id,
    unnest(data->>'$.specialisms[*].name') AS specialism
FROM raw_locations
WHERE data->>'registrationStatus' = 'Registered';
