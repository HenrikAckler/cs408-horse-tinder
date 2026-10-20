# Horse Tinder

A Flask and Jinja Horse Tinder application. Checkpoint 2 provides account registration, login/logout, and an editable personal profile. `/dependencies` reports whether the selected frontend libraries are available.

## Local setup

Prerequisites: Linux, Python 3.10 or newer, `python3-venv`, and pip. On Ubuntu, install them with `sudo apt install python3 python3-venv python3-pip`.

Run from the repository root:

```bash
./start.sh
```

The script creates a local virtual environment, installs the Python requirements, initializes the SQLite file and account/profile tables under `instance/`, and starts the site at http://localhost:5000/. A persistent local Flask session key is created at `instance/flask_secret_key` the first time the app runs. Keep this file private and do not commit it. Open `/dependencies` to check Flask, Jinja, SQLite, Bootstrap, Tailwind, Alpine.js, and Hammer.js. Frontend libraries are loaded from public CDNs, so that page needs network access in the browser.

## Accounts and profiles

Open the home page and choose **Create an account** or **Log in**. Registration requires a unique username (3–32 letters, numbers, dots, dashes, or underscores) and a password of at least 8 characters. Passwords are stored as bcrypt hashes. After registration or login, use **My profile** to edit your display name, breed/kind, age, interests, and optional HTTP(S) profile picture URL. The account username is fixed after registration. Use the navigation's **Log out** button to end the session.

SQLite creates `users` and `profiles` tables automatically when the app starts. The default database is `instance/horse_tinder.db`; set `HORSE_TINDER_DATABASE` to use another path.

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
