// force-reset.js - reset DB with real codes only
const Database = require('better-sqlite3');
const path = require('path');

const DB_PATH = path.join(__dirname, '..', 'data', 'codes.db');

const db = new Database(DB_PATH);
db.pragma('journal_mode = WAL');

db.exec('DROP TABLE IF EXISTS codes');
db.exec(`CREATE TABLE codes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    apple_url   TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'available',
    created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    used_at     TEXT,
    access_ip   TEXT,
    user_agent  TEXT
)`);
db.exec('CREATE INDEX IF NOT EXISTS idx_codes_status ON codes(status)');
db.exec('CREATE INDEX IF NOT EXISTS idx_codes_created ON codes(created_at)');

const codes = [
    "https://apps.apple.com/redeem?code=9RMA9HM9MFHM&ctx=apps",
    "https://apps.apple.com/redeem?code=8RMA9HM9MFHM&ctx=apps",
    "https://apps.apple.com/redeem?code=7RMA9HM9MFHM&ctx=apps",
];

const insert = db.prepare('INSERT INTO codes (apple_url) VALUES (?)');
for (const url of codes) insert.run(url);

const count = db.prepare('SELECT COUNT(*) AS cnt FROM codes').get();
console.log('✅ Reset OK: ' + count.cnt + ' real codes loaded');
db.close();
