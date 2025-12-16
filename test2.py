import sqlite3

connection = sqlite3.connect("morkborg.sqlite")
cursor = connection.cursor()

cursor.execute("SELECT * FROM classes;")

result = cursor.fetchall()

print(result)
