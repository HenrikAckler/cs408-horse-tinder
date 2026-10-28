CREATE TABLE IF NOT EXISTS logindata (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL COLLATE NOCASE UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Every matchable person/horse has the same profile shape. Login accounts link
-- to one row; seeded profiles have no login account.
CREATE TABLE IF NOT EXISTS profiledata (
    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    name TEXT,
    pfp TEXT,
    breed TEXT,
    age INTEGER CHECK (age IS NULL OR age BETWEEN 0 AND 200),
    interests TEXT,
    seed_key TEXT UNIQUE,
    FOREIGN KEY (user_id) REFERENCES logindata(user_id) ON DELETE CASCADE
);

-- A login account can swipe on any other profile row.
CREATE TABLE IF NOT EXISTS swipes (
    swipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    profile_id INTEGER NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('left', 'right')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, profile_id),
    FOREIGN KEY (user_id) REFERENCES logindata(user_id) ON DELETE CASCADE,
    FOREIGN KEY (profile_id) REFERENCES profiledata(profile_id) ON DELETE CASCADE
);
