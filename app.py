"""Minimal Flask foundation for Horse Tinder."""

import os
import sqlite3
from pathlib import Path

from flask import Flask, render_template

app = Flask(__name__)
DATABASE = Path(os.environ.get("HORSE_TINDER_DATABASE", "instance/horse_tinder.db"))


def initialize_database():
    """Create the SQLite database file so a fresh run is ready to use."""
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE) as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS setup_check (id INTEGER PRIMARY KEY)")


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/dependencies")
def dependencies():
    return render_template("dependencies.html")


@app.get("/api/health")
def health():
    return {"status": "ok"}, 200


initialize_database()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
