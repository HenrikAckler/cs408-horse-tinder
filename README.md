# Horse Tinder

A Flask and Jinja Horse Tinder application. Checkpoint 3 includes account registration, login/logout, editable personal profiles, and a matching page with sample horses, filters, and saved left/right swipes. `/dependencies` reports whether the selected frontend libraries are available.

## Local setup

Prerequisites: Linux, Python 3.10 or newer, `python3-venv`, and pip. On Ubuntu, install them with `sudo apt install python3 python3-venv python3-pip`.

Run from the repository root:

```bash
./start.sh
```

The script creates a local virtual environment, installs the Python requirements, initializes the SQLite file and tables under `instance/`, and starts the site at http://localhost:5000/. A persistent local Flask session key is created at `instance/flask_secret_key` the first time the app runs. Keep this file private and do not commit it. Open `/dependencies` to check Flask, Jinja, SQLite, Bootstrap, Tailwind, Alpine.js, and Hammer.js. Frontend libraries are loaded from public CDNs, so that page needs network access in the browser.

## Accounts and profiles

Open the home page and choose **Create an account** or **Log in**. Registration requires a unique username (3–32 letters, numbers, dots, dashes, or underscores) and a password of at least 8 characters. Passwords are stored as bcrypt hashes. After registration or login, use **My profile** to edit your display name, breed/kind, age, interests, and optional HTTP(S) profile picture URL. The account username is fixed after registration. Use the navigation's **Log out** button to end the session.

SQLite creates and updates the tables automatically when the app starts. The default database is `instance/horse_tinder.db`; set `HORSE_TINDER_DATABASE` to use another path. The schema is documented in `schema.sql` and below:

- `users` stores the login username and bcrypt password hash.
- `profiles` stores each account's personal profile; it is linked to `users` by `user_id`.
- `horses` stores the small, fixed set of sample horses. Startup inserts any missing sample IDs and does not replace existing rows.
- `swipes` stores each user's left/right decision for a horse. A unique `(user_id, horse_id)` constraint allows one decision per horse for each user; foreign keys remove related swipes if their account or horse is deleted.

## Matching

After signing up or logging in, open **Matching** to browse 50 sample horses. Filter by breed and optional minimum/maximum age, then swipe left to pass or right to like. You can also use the **Pass** and **Like** buttons. Horizontal gestures use the lightweight Hammer.js library, with Alpine.js connecting the gesture to the existing form. Decisions are saved to SQLite and that horse is removed from your deck for that account. Clearing filters does not clear swipes. Horse profile and chat buttons currently lead to checkpoint 4 placeholders.

The sample horse records are defined in `app.py` and seeded idempotently when the app initializes. Existing databases gain the `horses` and `swipes` tables on startup without deleting account, profile, or swipe data. See [`docs/checkpoint3.md`](docs/checkpoint3.md) for the implementation notes and database change details.

For local development, the app creates a persistent, private session key beside the configured database if `SECRET_KEY` is not set. On EC2, `deploy/setup-ec2.sh` creates `/etc/horse-tinder.env` with a stable random `SECRET_KEY`; the systemd service reads it on startup. The setup script preserves an existing file when run again. Keep that file readable only by root and the app's service group, and do not add the key to the repository.

## EC2 setup and deployment

Create an Ubuntu EC2 instance with SSH access and configure its security group to allow inbound SSH on port 22 and HTTP on port 80. From the repository root on your laptop, deploy with:

```bash
HOST="your-instance-public-dns-or-ip"
KEY="$HOME/.ssh/henrikackler-cs408-k1.pem"
./deploy/deploy.sh -h "$HOST" -i "$KEY"
```

The first run automatically installs the server runtime and Nginx, creates a persistent session key, configures the systemd service, uploads the app, initializes its database, and checks `/api/health`. Later runs reuse the setup and deploy the latest code. The session key stays on the server and is not copied from your laptop.

When deployment succeeds, open `http://<current EC2 public DNS name or IP>/`. If the instance is stopped and started, AWS may assign it a new public address; use the current address for the next deploy.
