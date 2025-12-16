import sqlite3

DB_PATH = "morkborg.sqlite"


def get_connection():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con
