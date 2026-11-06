import duckdb

con = duckdb.connect("data/cqc.duckdb")

con.execute(open("sql/01_raw.sql").read())
con.execute(open("sql/02_staging.sql").read())

con.sql("SELECT count(*) FROM raw_locations").show()
con.sql("SELECT count(*) FROM stg_locations").show()
