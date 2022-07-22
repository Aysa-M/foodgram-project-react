import csv
import sqlite3

con = sqlite3.connect(
    'C:\\Dev\\foodgram-project-react\\backend\\foodgram\\db.sqlite3'
)
cur = con.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS recipes_ingredient (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            measurement_unit TEXT
)""")

with open(
    'C:\\Dev\\foodgram-project-react\\data\\ingredients.csv',
    'r',
    encoding="utf8"
) as f:
    dr = csv.DictReader(f, delimiter=",")
    to_db = [(i['name'], i['measurement_unit']) for i in dr]

cur.executemany(
    "INSERT OR IGNORE INTO recipes_ingredient (name, measurement_unit) VALUES"
    " (?, ?);", to_db)
con.commit()
con.close()
