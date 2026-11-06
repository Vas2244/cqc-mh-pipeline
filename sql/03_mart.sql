-- one line of specialisms per service
-- (joining straight to stg_specialisms turned 158 services into 649 rows, so I group first)
CREATE OR REPLACE TABLE specialisms_per_service AS
SELECT location_id, string_agg(specialism, '; ' ORDER BY specialism) AS specialisms
FROM stg_specialisms
GROUP BY location_id;

-- same for service types
CREATE OR REPLACE TABLE service_types_per_service AS
SELECT location_id, string_agg(service_type, '; ' ORDER BY service_type) AS service_types
FROM stg_service_types
GROUP BY location_id;

-- mart 1: one row per service, for the finder and map
CREATE OR REPLACE TABLE mart_services AS
SELECT
    l.*,
    t.service_types,
    s.specialisms
FROM stg_locations l
LEFT JOIN service_types_per_service t ON l.location_id = t.location_id
LEFT JOIN specialisms_per_service s ON l.location_id = s.location_id;

-- all 33 London areas
-- (only 32 have a service, so without this list the empty one would just disappear)
CREATE OR REPLACE TABLE london_boroughs AS
SELECT * FROM (VALUES
    ('Barking and Dagenham'), ('Barnet'), ('Bexley'), ('Brent'), ('Bromley'),
    ('Camden'), ('City of London'), ('Croydon'), ('Ealing'), ('Enfield'),
    ('Greenwich'), ('Hackney'), ('Hammersmith and Fulham'), ('Haringey'), ('Harrow'),
    ('Havering'), ('Hillingdon'), ('Hounslow'), ('Islington'), ('Kensington and Chelsea'),
    ('Kingston upon Thames'), ('Lambeth'), ('Lewisham'), ('Merton'), ('Newham'),
    ('Redbridge'), ('Richmond upon Thames'), ('Southwark'), ('Sutton'), ('Tower Hamlets'),
    ('Waltham Forest'), ('Wandsworth'), ('Westminster')
) AS t(borough);

-- how many services each borough has for each specialism
CREATE OR REPLACE TABLE borough_specialism_counts AS
SELECT l.borough, s.specialism, count(*) AS services
FROM stg_specialisms s
JOIN stg_locations l ON s.location_id = l.location_id
GROUP BY l.borough, s.specialism;

-- mart 2: every borough with every specialism, 0 where none is registered
CREATE OR REPLACE TABLE mart_gaps AS
SELECT
    b.borough,
    sp.specialism,
    coalesce(c.services, 0) AS services
FROM london_boroughs b
CROSS JOIN (SELECT DISTINCT specialism FROM stg_specialisms) sp
LEFT JOIN borough_specialism_counts c
    ON c.borough = b.borough AND c.specialism = sp.specialism;


-- ---------- summary tables for the app ----------
-- one summary table per dashboard question, so all the counting happens in SQL

-- the 4 headline numbers, one row
CREATE OR REPLACE TABLE mart_summary AS
SELECT
    count(*) AS services,
    count(*) FILTER (WHERE run_by = 'NHS') AS nhs,
    count(*) FILTER (WHERE run_by = 'Independent') AS independent,
    round(100.0 * count(*) FILTER (WHERE run_by = 'Independent') / count(*)) AS pct_independent,
    count(DISTINCT borough) AS boroughs_with_service
FROM mart_services;

-- services per borough, split by who runs them
CREATE OR REPLACE TABLE mart_borough_run_by AS
SELECT borough, run_by, count(*) AS services
FROM mart_services
GROUP BY borough, run_by;

-- services per specialism, split by who runs them
-- (a service with 3 specialisms counts once in each)
CREATE OR REPLACE TABLE mart_specialism_run_by AS
SELECT s.specialism, l.run_by, count(*) AS services
FROM stg_specialisms s
JOIN stg_locations l ON s.location_id = l.location_id
GROUP BY s.specialism, l.run_by;

-- services per ICB, split by who runs them
-- (2 services have no ICB in the data, so they're left out here)
CREATE OR REPLACE TABLE mart_icb_run_by AS
SELECT icb, run_by, count(*) AS services
FROM mart_services
WHERE icb IS NOT NULL
GROUP BY icb, run_by;

-- for each specialism, how many of the 33 boroughs have none
CREATE OR REPLACE TABLE mart_gaps_summary AS
SELECT specialism, count(*) AS boroughs_with_none
FROM mart_gaps
WHERE services = 0
GROUP BY specialism;
