CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL COLLATE NOCASE UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS profiles (
    user_id INTEGER PRIMARY KEY,
    display_name TEXT,
    pfp TEXT,
    breed TEXT,
    age INTEGER CHECK (age IS NULL OR age BETWEEN 0 AND 200),
    interests TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Sample horses shown on the matching page. Seeded rows use stable IDs.
CREATE TABLE IF NOT EXISTS horses (
    horse_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    breed TEXT NOT NULL,
    age INTEGER NOT NULL CHECK (age BETWEEN 0 AND 80),
    interests TEXT NOT NULL,
    pfp TEXT
);

-- One saved left/right decision per user and horse.
CREATE TABLE IF NOT EXISTS swipes (
    swipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    horse_id INTEGER NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('left', 'right')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, horse_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (horse_id) REFERENCES horses(horse_id) ON DELETE CASCADE
);
