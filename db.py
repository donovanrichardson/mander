import sqlite3

con = sqlite3.connect(':memory:', isolation_level=None)

# cur = con.cursor()

# cur.execute('select * from node')
# rows = cur.fetchall()
# print(rows)

# cur.close()

# # con.close()