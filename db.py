import sqlite3
from flask import g
import os

DATABASE = "feed.db"

def get_db():
    if "db" not in g:
        dir_name = os.path.dirname(DATABASE)
        if dir_name:  # only create folder if a directory exists
            os.makedirs(dir_name, exist_ok=True)
        db = sqlite3.connect(DATABASE, timeout=30, check_same_thread=False)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL;")
        db.execute("PRAGMA synchronous=NORMAL;")
        db.execute("PRAGMA foreign_keys=ON;")
        g.db = db
    return g.db
