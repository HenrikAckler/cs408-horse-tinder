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

These commands use the current instance hostname and key path. Run the laptop commands in a terminal on your Debian machine, from the repository root. The `-h` argument is only the hostname: the deploy script supplies the `ubuntu@` login itself.

### One-time server setup

First copy the setup files from your laptop to the server:

```bash
scp -i "$HOME/.ssh/henrikackler-cs408-k1.pem" -r deploy ubuntu@ec2-34-221-30-167.us-west-2.compute.amazonaws.com:~
```

Connect to the server:

```bash
ssh -i "$HOME/.ssh/henrikackler-cs408-k1.pem" ubuntu@ec2-34-221-30-167.us-west-2.compute.amazonaws.com
```

Now you are in a shell on the EC2 instance. Run the setup script there:

```bash
sudo bash deploy/setup-ec2.sh
```

When setup finishes, leave the EC2 shell with `exit` to return to your laptop terminal.

### Deploy the app

From the repository root on your laptop, run:

```bash
./deploy/deploy.sh -h ec2-34-221-30-167.us-west-2.compute.amazonaws.com -i "$HOME/.ssh/henrikackler-cs408-k1.pem"
```

The script copies the app to EC2, installs its Python requirements, restarts the systemd service, and checks `/api/health`. When it reports success, open http://ec2-34-221-30-167.us-west-2.compute.amazonaws.com/ in a browser. The EC2 security group must allow inbound SSH on port 22 and HTTP on port 80.

If the instance is stopped and started, AWS may assign it a new public hostname. Replace the hostname in these commands and the browser URL with the instance's current public DNS name. Keep `ubuntu@` in the `scp` and `ssh` commands; omit it from the deploy script's `-h` value.
