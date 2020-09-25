import psycopg2

con = psycopg2.connect(
    host = 'localhost',
    database='mander',
    user='',
    password=''
)

con.autocommit = True

# cur = con.cursor()

# cur.execute('select * from node')
# rows = cur.fetchall()
# print(rows)

# cur.close()

# # con.close()