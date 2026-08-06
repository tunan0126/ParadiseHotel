import sqlite3
c = sqlite3.connect('hotel.db')
print(c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
