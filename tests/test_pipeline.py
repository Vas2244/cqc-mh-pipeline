import glob
import duckdb

con = duckdb.connect("data/cqc.duckdb", read_only=True)


def count(sql):
    return con.sql(sql).fetchall()[0][0]


def test_mart_is_not_empty():
    assert count("SELECT count(*) FROM mart_services") > 0


def test_every_raw_file_is_loaded():
    files = len(glob.glob("data/raw/*.json"))
    rows = count("SELECT count(*) FROM raw_locations")
    assert rows == files


def test_service_ids_are_unique_and_not_empty():
    rows = count("SELECT count(*) FROM stg_locations")
    unique_ids = count("SELECT count(DISTINCT location_id) FROM stg_locations")
    empty_ids = count("SELECT count(*) FROM stg_locations WHERE location_id IS NULL")
    assert rows == unique_ids
    assert empty_ids == 0


def test_only_current_services():
    # most of the raw data had closed, so staging should only keep the registered ones
    registered = count("SELECT count(*) FROM raw_locations WHERE data->>'registrationStatus' = 'Registered'")
    staged = count("SELECT count(*) FROM stg_locations")
    assert staged == registered


def test_no_fan_out():
    # joining to specialisms used to turn 158 services into 649 rows
    services = count("SELECT count(*) FROM stg_locations")
    mart_rows = count("SELECT count(*) FROM mart_services")
    assert mart_rows == services


def test_gaps_has_all_33_boroughs():
    # one borough has no services, so it would disappear without the borough list
    boroughs = count("SELECT count(DISTINCT borough) FROM mart_gaps")
    assert boroughs == 33
