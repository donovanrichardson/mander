import sqlite3

sqlite3.enable_callback_tracebacks(True)

con = sqlite3.connect(':memory:', isolation_level=None)

# cur = con.cursor()

# cur.execute('select * from node')
# rows = cur.fetchall()
# print(rows)

# cur.close()

# # con.close()