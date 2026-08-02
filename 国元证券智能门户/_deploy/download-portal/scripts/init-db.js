const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');

const DATA_DIR = path.join(__dirname, '..', 'data');
const DB_PATH = path.join(DATA_DIR, 'codes.db');

if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

const db = new Database(DB_PATH);

db.pragma('journal_mode = WAL');

db.exec(`
  CREATE TABLE IF NOT EXISTS codes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    apple_url   TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'available',
    created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    used_at     TEXT,
    access_ip   TEXT,
    user_agent  TEXT
  )
`);

db.exec(`
  CREATE INDEX IF NOT EXISTS idx_codes_status ON codes(status);
`);
db.exec(`
  CREATE INDEX IF NOT EXISTS idx_codes_created ON codes(created_at);
`);

const count = db.prepare('SELECT COUNT(*) AS cnt FROM codes').get();
if (count.cnt === 0) {
  const insert = db.prepare('INSERT INTO codes (apple_url) VALUES (?)');
  const insertMany = db.transaction((items) => {
    for (const url of items) {
      insert.run(url);
    }
  });

  const mockUrls = [];
  for (let i = 1; i <= 10; i++) {
    mockUrls.push(`https://apps.apple.com/redeem?ctx=offercodes&id=123456789&code=TEST${String(i).padStart(2, '0')}`);
  }
  insertMany(mockUrls);
  console.log(`已插入 ${mockUrls.length} 条模拟兑换链接`);
} else {
  console.log(`数据库已有 ${count.cnt} 条记录，跳过初始化`);
}

db.close();
console.log('数据库初始化完成');
