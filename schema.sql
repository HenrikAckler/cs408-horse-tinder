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

CREATE TABLE IF NOT EXISTS chats (
    chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id_0 INTEGER NOT NULL,
    profile_id_1 INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (profile_id_0 < profile_id_1),
    UNIQUE (profile_id_0, profile_id_1),
    FOREIGN KEY (profile_id_0) REFERENCES profiledata(profile_id) ON DELETE CASCADE,
    FOREIGN KEY (profile_id_1) REFERENCES profiledata(profile_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chat_participants (
    chat_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    deleted_at TEXT,
    PRIMARY KEY (chat_id, user_id),
    FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES logindata(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chat_messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    sender_profile_id INTEGER NOT NULL,
    body TEXT NOT NULL CHECK (length(body) BETWEEN 1 AND 2000),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE,
    FOREIGN KEY (sender_profile_id) REFERENCES profiledata(profile_id) ON DELETE CASCADE
);

-- Feed authors reuse profiledata, so sample horses and account holders share one shape.
CREATE TABLE IF NOT EXISTS feed_posts (
    post_id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    image_path TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    seed_key TEXT UNIQUE,
    FOREIGN KEY (profile_id) REFERENCES profiledata(profile_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS feed_posts_created
    ON feed_posts(created_at DESC, post_id DESC);

CREATE INDEX IF NOT EXISTS chat_messages_chat_created
    ON chat_messages(chat_id, created_at, message_id);
