import sqlite3
import pandas as pd

conn = sqlite3.connect("test_db.sqlite")
df = pd.read_sql_query("SELECT * FROM customers LIMIT 50;", conn)
print(df)
conn.close()
