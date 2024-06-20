import csv
import psycopg2

conn = psycopg2.connect("postgres://lego_land_db_user:K1rQJJ78QA38zeRuiV2DvNZ8MnWU3mzA@dpg-cppuandds78s73ef0480-a.oregon-postgres.render.com/lego_land_db")
cur = conn.cursor()

with open('./seed_data/themes.csv', 'r') as f:
    reader = csv.reader(f)
    next(reader)  # Skip the header row
    for row in reader:
        cur.execute(
            "INSERT INTO theme (id, title, quantity) VALUES (%s, %s, %s)",
            row
        )

conn.commit()
cur.close()
conn.close()
