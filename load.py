import duckdb

con = duckdb.connect("data/cqc.duckdb")

sql = open("sql/01_raw.sql").read()
con.execute(sql)

con.sql("SELECT count(*) FROM raw_locations").show()
