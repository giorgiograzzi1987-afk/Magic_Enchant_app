-- Magic_Enchant schema (SQLite)

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS spells (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    level INTEGER NOT NULL,
    school TEXT,
    ritual INTEGER DEFAULT 0,
    concentration INTEGER DEFAULT 0,
    casting_time TEXT,
    range TEXT,
    components TEXT,
    material TEXT,
    duration TEXT,
    classes TEXT,
    description TEXT,
    higher_level TEXT,
    source TEXT,
    url TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS spell_status (
    spell_id INTEGER PRIMARY KEY,
    known INTEGER DEFAULT 0,
    prepared INTEGER DEFAULT 0,
    favorite INTEGER DEFAULT 0,
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (spell_id) REFERENCES spells(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS character_profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    class_name TEXT,
    level INTEGER DEFAULT 1
);

INSERT OR IGNORE INTO character_profile (id, class_name, level)
VALUES (1, NULL, 1);
