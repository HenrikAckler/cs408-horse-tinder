"""Horse Tinder Flask application."""

import os
import re
import secrets
import sqlite3
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from urllib.parse import urlparse

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect

ROOT = Path(__file__).resolve().parent
DATABASE = Path(os.environ.get("HORSE_TINDER_DATABASE", ROOT / "instance/horse_tinder.db"))
SCHEMA = ROOT / "schema.sql"
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")
MAX_PASSWORD_BYTES = 72  # bcrypt's portable input limit

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY") or "",
    WTF_CSRF_TIME_LIMIT=3600,
)
bcrypt = Bcrypt(app)
CSRFProtect(app)


def _secret_key():
    """Use the configured production key or create a persistent local key."""
    configured_key = os.environ.get("SECRET_KEY")
    if configured_key:
        return configured_key

    key_path = DATABASE.parent / "flask_secret_key"
    key_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        key = key_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        key = secrets.token_urlsafe(48)
        try:
            descriptor = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            key = key_path.read_text(encoding="utf-8").strip()
        else:
            with os.fdopen(descriptor, "w", encoding="utf-8") as secret_file:
                secret_file.write(key + "\n")
    if not key:
        raise RuntimeError(f"The Flask session secret at {key_path} is empty.")
    return key


app.config["SECRET_KEY"] = _secret_key()


@contextmanager
def get_db():
    """Open a configured SQLite connection with named row access and FKs."""
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database():
    """Create database tables when needed without discarding existing data."""
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as connection:
        connection.executescript(SCHEMA.read_text(encoding="utf-8"))


def get_user_by_id(user_id):
    with get_db() as connection:
        return connection.execute(
            "SELECT user_id, username FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if not session.get("user_id") or get_user_by_id(session["user_id"]) is None:
            session.clear()
            flash("Please log in to view your profile.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(**kwargs)

    return wrapped_view


def valid_local_redirect(target):
    """Accept only a same-site path as a post-login redirect destination."""
    if not target:
        return None
    parsed = urlparse(target)
    if (
        parsed.scheme
        or parsed.netloc
        or not target.startswith("/")
        or target.startswith("//")
        or "\\" in target
    ):
        return None
    return target


@app.context_processor
def inject_current_user():
    user_id = session.get("user_id")
    return {"current_user": get_user_by_id(user_id) if user_id else None}


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/register")
def register():
    if session.get("user_id") and get_user_by_id(session["user_id"]):
        return redirect(url_for("profile"))
    return render_template("register.html")


@app.post("/register")
def register_submit():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not USERNAME_PATTERN.fullmatch(username):
        flash("Username must be 3–32 characters and use only letters, numbers, dots, dashes, or underscores.", "danger")
        return render_template("register.html", username=username), 400
    if len(password.encode("utf-8")) < 8 or len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        flash("Password must be at least 8 characters and no more than 72 UTF-8 bytes.", "danger")
        return render_template("register.html", username=username), 400
    if password != confirm_password:
        flash("The password confirmation does not match.", "danger")
        return render_template("register.html", username=username), 400

    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    try:
        with get_db() as connection:
            cursor = connection.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash),
            )
            user_id = cursor.lastrowid
            connection.execute("INSERT INTO profiles (user_id) VALUES (?)", (user_id,))
    except sqlite3.IntegrityError:
        flash("That username is already in use. Please choose another.", "danger")
        return render_template("register.html", username=username), 400

    session.clear()
    session["user_id"] = user_id
    flash("Your account is ready. Add a few details to your profile.", "success")
    return redirect(url_for("profile"))


@app.get("/login")
def login():
    if session.get("user_id") and get_user_by_id(session["user_id"]):
        return redirect(url_for("profile"))
    return render_template("login.html", next=valid_local_redirect(request.args.get("next")))


@app.post("/login")
def login_submit():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    with get_db() as connection:
        user = connection.execute(
            "SELECT user_id, username, password_hash FROM users WHERE username = ? COLLATE NOCASE",
            (username,),
        ).fetchone()

    if user is None or not bcrypt.check_password_hash(user["password_hash"], password):
        flash("Username or password is incorrect.", "danger")
        return render_template(
            "login.html", username=username,
            next=valid_local_redirect(request.form.get("next")),
        ), 401

    session.clear()
    session["user_id"] = user["user_id"]
    flash("You are signed in.", "success")
    destination = valid_local_redirect(request.form.get("next"))
    return redirect(destination or url_for("profile"))


@app.post("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("index"))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user_id = session["user_id"]
    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip()
        breed = request.form.get("breed", "").strip()
        age_text = request.form.get("age", "").strip()
        interests = request.form.get("interests", "").strip()
        pfp = request.form.get("pfp", "").strip()

        if len(display_name) > 80 or len(breed) > 80 or len(interests) > 2000:
            flash("Please keep the name and breed under 80 characters and interests under 2,000 characters.", "danger")
            return _render_profile(user_id, 400, request.form)
        age = None
        if age_text:
            try:
                age = int(age_text)
            except ValueError:
                flash("Age must be a whole number between 0 and 200.", "danger")
                return _render_profile(user_id, 400, request.form)
            if not 0 <= age <= 200:
                flash("Age must be a whole number between 0 and 200.", "danger")
                return _render_profile(user_id, 400, request.form)
        if pfp and (len(pfp) > 2048 or urlparse(pfp).scheme not in {"http", "https"} or not urlparse(pfp).netloc):
            flash("Profile picture must be a valid HTTP or HTTPS image URL.", "danger")
            return _render_profile(user_id, 400, request.form)

        with get_db() as connection:
            connection.execute(
                """UPDATE profiles
                   SET display_name = ?, breed = ?, age = ?, interests = ?, pfp = ?
                   WHERE user_id = ?""",
                (display_name or None, breed or None, age, interests or None, pfp or None, user_id),
            )
        flash("Your profile has been saved.", "success")
        return redirect(url_for("profile"))

    return _render_profile(user_id)


def _render_profile(user_id, status=200, form_values=None):
    with get_db() as connection:
        data = connection.execute(
            """SELECT users.username, profiles.display_name, profiles.pfp,
                      profiles.breed, profiles.age, profiles.interests
               FROM users JOIN profiles USING (user_id)
               WHERE users.user_id = ?""",
            (user_id,),
        ).fetchone()
    if data is None:
        abort(404)
    return render_template("profile.html", profile=data, form_values=form_values), status


@app.get("/dependencies")
def dependencies():
    return render_template("dependencies.html")


@app.get("/api/health")
def health():
    return {"status": "ok"}, 200


initialize_database()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
