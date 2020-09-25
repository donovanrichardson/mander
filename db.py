import psycopg2

con = psycopg2.connect(
    host = 'localhost',
    database='mander',
    user='',
    password=''
)

cur = con.cursor()

cur.execute('select * from node')
rows = cur.fetchall()
print(rows)

cur.close()

con.close()