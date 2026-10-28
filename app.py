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
SAMPLE_HORSES = (
    (1, "Muffin", "Shetland Pony", 8, "Carrots, small jumps, naps", None),
    (2, "Dusty", "Quarter Horse", 11, "Trail rides, sunny fields", None),
    (3, "Juniper", "Arabian", 6, "Long walks, apples, attention", None),
    (4, "Pickles", "Appaloosa", 9, "Rolling in grass, making friends", None),
    (5, "Clover", "Morgan", 5, "Learning tricks, crunchy treats", None),
    (6, "Thunder", "Mustang", 14, "Open pastures, quiet company", None),
    (7, "Biscuit", "Welsh Pony", 7, "Forest trails, grooming, pears", None),
    (8, "Marigold", "Paint Horse", 10, "Creek splashing, slow mornings", None),
    (9, "Rocket", "Thoroughbred", 4, "Running fast, sunflower seeds", None),
    (10, "Bluebell", "Connemara", 12, "Hacking, cuddles, fresh hay", None),
    (11, "Waffles", "Haflinger", 9, "Carriage rides, beach walks", None),
    (12, "Poppy", "Tennessee Walker", 13, "Gentle trails, making people smile", None),
    (13, "Bandit", "Gypsy Vanner", 8, "Long manes, music, carrots", None),
    (14, "Olive", "Standardbred", 6, "Trotting, apples, quiet friends", None),
    (15, "Nacho", "Miniature Horse", 5, "Tiny jumps, big snacks", None),
    (16, "Willow", "Friesian", 11, "Dressage, shiny coats, apples", None),
    (17, "Pancake", "Clydesdale", 15, "Parades, brushing, naps", None),
    (18, "Cinnamon", "Mustang", 3, "New adventures, sweet grass", None),
    (19, "Mochi", "Shetland Pony", 18, "Being adorable, stealing hats", None),
    (20, "Sundance", "Quarter Horse", 7, "Ranch work, open spaces", None),
    (21, "Fern", "Morgan", 16, "Quiet companionship, clover", None),
    (22, "Pretzel", "Appaloosa", 6, "Obstacle courses, rolling", None),
    (23, "Skittles", "Arabian", 9, "Long rides, singing birds", None),
    (24, "Doodle", "Welsh Pony", 14, "Teaching kids, snack breaks", None),
    (25, "Maple", "Paint Horse", 5, "Autumn leaves, trail rides", None),
    (26, "Socks", "Thoroughbred", 8, "Morning runs, peppermints", None),
    (27, "Daisy", "Connemara", 4, "Jumping, paddock friends", None),
    (28, "Gingersnap", "Haflinger", 17, "Cozy blankets, carrots", None),
    (29, "Comet", "Tennessee Walker", 10, "Night skies, smooth trails", None),
    (30, "Bramble", "Gypsy Vanner", 13, "Woodland walks, gentle pats", None),
    (31, "Peaches", "Standardbred", 7, "Peach slices, trotting", None),
    (32, "Tater Tot", "Miniature Horse", 11, "Tiny adventures, attention", None),
    (33, "Velvet", "Friesian", 6, "Elegant walks, mane braiding", None),
    (34, "Big Mac", "Clydesdale", 9, "Pulling carts, friendly waves", None),
    (35, "Ranger", "Mustang", 19, "Wide open fields, sunsets", None),
    (36, "Toffee", "Quarter Horse", 2, "Learning new things, treats", None),
    (37, "Sage", "Morgan", 8, "Easy rides, cool weather", None),
    (38, "Confetti", "Appaloosa", 12, "Parties, patterned blankets", None),
    (39, "Starlight", "Arabian", 15, "Moonlit rides, quiet barns", None),
    (40, "Pebbles", "Shetland Pony", 3, "Puddles, tiny carrots", None),
    (41, "Rio", "Paint Horse", 16, "River walks, friendly races", None),
    (42, "Whiskey", "Thoroughbred", 12, "Retirement, soft hay", None),
    (43, "Luna", "Connemara", 7, "Cross-country, dandelions", None),
    (44, "Noodle", "Haflinger", 5, "Following friends, snack time", None),
    (45, "Echo", "Tennessee Walker", 18, "Slow rides, birdsong", None),
    (46, "Fable", "Gypsy Vanner", 2, "Meeting new friends, apples", None),
    (47, "Pistachio", "Standardbred", 14, "Easy trots, green grass", None),
    (48, "Button", "Miniature Horse", 8, "Pocket-sized adventures", None),
    (49, "Regal", "Friesian", 17, "Gentle dressage, grooming", None),
    (50, "Huckleberry", "Clydesdale", 4, "Meadow walks, crunchy snacks", None),
)

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
    """Create tables and idempotently add the sample profiles."""
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as connection:
        connection.executescript(SCHEMA.read_text(encoding="utf-8"))
        connection.executemany(
            """INSERT OR IGNORE INTO profiledata
               (name, breed, age, interests, pfp, seed_key)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [
                (name, breed, age, interests, pfp, f"sample-profile-{sample_id:02d}")
                for sample_id, name, breed, age, interests, pfp in SAMPLE_HORSES
            ],
        )


def get_user_by_id(user_id):
    """Return the public account fields used by navigation, if it exists."""
    with get_db() as connection:
        return connection.execute(
            "SELECT user_id, username FROM logindata WHERE user_id = ?", (user_id,)
        ).fetchone()


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if not session.get("user_id") or get_user_by_id(session["user_id"]) is None:
            session.clear()
            flash("Please log in to continue.", "warning")
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
    """Render the public landing page."""
    return render_template("index.html")


@app.get("/register")
def register():
    """Show the account form, redirecting signed-in users to matching."""
    if session.get("user_id") and get_user_by_id(session["user_id"]):
        return redirect(url_for("matching"))
    return render_template("register.html")


@app.post("/register")
def register_submit():
    """Validate credentials, create an account, and start its session."""
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
                "INSERT INTO logindata (username, password_hash) VALUES (?, ?)",
                (username, password_hash),
            )
            user_id = cursor.lastrowid
            connection.execute(
                "INSERT INTO profiledata (user_id) VALUES (?)",
                (user_id,),
            )
    except sqlite3.IntegrityError:
        flash("That username is already in use. Please choose another.", "danger")
        return render_template("register.html", username=username), 400

    session.clear()
    session["user_id"] = user_id
    flash("Your account is ready. Add a few details to your profile.", "success")
    return redirect(url_for("matching"))


@app.get("/login")
def login():
    """Show the login form and preserve a safe local destination."""
    if session.get("user_id") and get_user_by_id(session["user_id"]):
        return redirect(url_for("matching"))
    return render_template("login.html", next=valid_local_redirect(request.args.get("next")))


@app.post("/login")
def login_submit():
    """Check credentials and begin a signed-in session."""
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    with get_db() as connection:
        user = connection.execute(
            "SELECT user_id, username, password_hash FROM logindata WHERE username = ? COLLATE NOCASE",
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
    return redirect(destination or url_for("matching"))


@app.post("/logout")
def logout():
    """Clear the signed-in session."""
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("index"))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Display or update only the profile owned by the signed-in account."""
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
                """UPDATE profiledata
                   SET name = ?, breed = ?, age = ?, interests = ?, pfp = ?
                   WHERE user_id = ?""",
                (display_name or None, breed or None, age, interests or None, pfp or None, user_id),
            )
        flash("Your profile has been saved.", "success")
        return redirect(url_for("profile"))

    return _render_profile(user_id)


def _render_profile(user_id, status=200, form_values=None):
    """Load and render one profile, preserving invalid submitted form values."""
    with get_db() as connection:
        data = connection.execute(
            """SELECT logindata.username, profiledata.name AS display_name, profiledata.pfp,
                      profiledata.breed, profiledata.age, profiledata.interests
               FROM logindata JOIN profiledata USING (user_id)
               WHERE logindata.user_id = ?""",
            (user_id,),
        ).fetchone()
    if data is None:
        abort(404)
    return render_template("profile.html", profile=data, form_values=form_values), status


@app.get("/matching")
@login_required
def matching():
    """Show the next other profile the signed-in user has not swiped on."""
    breed = request.args.get("breed", "").strip()
    min_age = _optional_age_filter("min_age")
    max_age = _optional_age_filter("max_age")
    min_age_input = request.args.get("min_age", "")
    max_age_input = request.args.get("max_age", "")
    if min_age is None and request.args.get("min_age", "").strip():
        min_age = 0
        flash("Minimum age must be a number from 0 to 200.", "warning")
    if max_age is None and request.args.get("max_age", "").strip():
        max_age = 200
        flash("Maximum age must be a number from 0 to 200.", "warning")
    if min_age is not None and max_age is not None and min_age > max_age:
        min_age, max_age = max_age, min_age
        min_age_input, max_age_input = str(min_age), str(max_age)
        flash("The age range was reversed, so it has been corrected.", "info")

    conditions = [
        "(profiledata.user_id IS NULL OR profiledata.user_id != ?)",
        "NOT EXISTS (SELECT 1 FROM swipes WHERE swipes.profile_id = profiledata.profile_id AND swipes.user_id = ?)",
    ]
    values = [session["user_id"], session["user_id"]]
    if breed:
        conditions.append("breed = ?")
        values.append(breed)
    if min_age is not None:
        conditions.append("age >= ?")
        values.append(min_age)
    if max_age is not None:
        conditions.append("age <= ?")
        values.append(max_age)

    with get_db() as connection:
        match_profile = connection.execute(
            """SELECT profiledata.profile_id, profiledata.user_id, profiledata.pfp,
                      profiledata.breed, profiledata.age, profiledata.interests,
                      COALESCE(profiledata.name, logindata.username, 'Unnamed profile') AS display_name
               FROM profiledata LEFT JOIN logindata USING (user_id)
               WHERE """
            + " AND ".join(conditions) + " ORDER BY profile_id LIMIT 1",
            values,
        ).fetchone()
        breeds = connection.execute(
            """SELECT DISTINCT breed FROM profiledata
               WHERE (user_id IS NULL OR user_id != ?) AND breed IS NOT NULL ORDER BY breed""",
            (session["user_id"],),
        ).fetchall()
        remaining = connection.execute(
            "SELECT COUNT(*) FROM profiledata WHERE " + " AND ".join(conditions), values,
        ).fetchone()[0]
        all_remaining = connection.execute(
            """SELECT COUNT(*) FROM profiledata
               WHERE (user_id IS NULL OR user_id != ?)
                 AND NOT EXISTS (SELECT 1 FROM swipes WHERE swipes.profile_id = profiledata.profile_id AND swipes.user_id = ?)""",
            (session["user_id"], session["user_id"]),
        ).fetchone()[0]
    return render_template(
        "matching.html", match_profile=match_profile, breeds=breeds, breed=breed,
        min_age=min_age_input, max_age=max_age_input,
        remaining=remaining, all_remaining=all_remaining,
    )


def _optional_age_filter(field):
    """Return a valid optional profile age filter, or None when blank/invalid."""
    raw_value = request.args.get(field, "").strip()
    if not raw_value:
        return None
    try:
        age = int(raw_value)
    except ValueError:
        return None
    return age if 0 <= age <= 200 else None


@app.post("/matching/swipe")
@login_required
def save_swipe():
    """Save a left/right decision, then return to the same filtered deck."""
    profile_id = request.form.get("profile_id", type=int)
    decision = request.form.get("decision") or request.form.get("gesture_decision", "")
    if profile_id is None or decision not in {"left", "right"}:
        abort(400)
    try:
        with get_db() as connection:
            cursor = connection.execute(
                """INSERT INTO swipes (user_id, profile_id, decision)
                   SELECT ?, profile_id, ? FROM profiledata
                   WHERE profile_id = ? AND (user_id IS NULL OR user_id != ?)""",
                (session["user_id"], decision, profile_id, session["user_id"]),
            )
            if cursor.rowcount == 0:
                abort(404)
    except sqlite3.IntegrityError:
        # A repeated submission is harmless; the unique key preserves the first choice.
        flash("You have already swiped on that profile.", "info")
    else:
        flash("You liked this profile!" if decision == "right" else "Profile skipped.", "success" if decision == "right" else "info")
    return redirect(url_for(
        "matching", breed=request.form.get("breed", ""),
        min_age=request.form.get("min_age", ""), max_age=request.form.get("max_age", ""),
    ))


@app.get("/checkpoint4/profile/<int:profile_id>")
@login_required
def matched_profile_placeholder(profile_id):
    """Provide a destination until read-only matched profiles arrive in checkpoint 4."""
    with get_db() as connection:
        profile = connection.execute(
            "SELECT profiledata.name, logindata.username FROM profiledata LEFT JOIN logindata USING (user_id) WHERE profile_id = ?",
            (profile_id,),
        ).fetchone()
    if profile is None:
        abort(404)
    return render_template("coming_soon.html", feature=f"{profile['name'] or profile['username'] or 'Profile'}'s profile")


@app.get("/checkpoint4/chat/<int:profile_id>")
@login_required
def matched_profile_chat_placeholder(profile_id):
    """Provide a destination until matched-profile chats arrive in checkpoint 4."""
    with get_db() as connection:
        profile = connection.execute(
            "SELECT profiledata.name, logindata.username FROM profiledata LEFT JOIN logindata USING (user_id) WHERE profile_id = ?",
            (profile_id,),
        ).fetchone()
    if profile is None:
        abort(404)
    return render_template("coming_soon.html", feature=f"Chat with {profile['name'] or profile['username'] or 'this profile'}")


@app.get("/dependencies")
def dependencies():
    """Render the page that reports selected app dependencies."""
    return render_template("dependencies.html")


@app.get("/api/health")
def health():
    """Return the lightweight status response used by deployment checks."""
    return {"status": "ok"}, 200


initialize_database()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
