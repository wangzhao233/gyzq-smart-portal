const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');

const DATA_DIR = path.join(__dirname, 'data');
const DB_PATH = path.join(DATA_DIR, 'codes.db');

if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

const db = new Database(DB_PATH);
db.pragma('journal_mode = WAL');

function getStats() {
  const total = db.prepare('SELECT COUNT(*) AS cnt FROM codes').get();
  const used = db.prepare("SELECT COUNT(*) AS cnt FROM codes WHERE status = 'used'").get();
  const available = db.prepare("SELECT COUNT(*) AS cnt FROM codes WHERE status = 'available'").get();
  const todayUsed = db.prepare(
    "SELECT COUNT(*) AS cnt FROM codes WHERE status = 'used' AND date(used_at) = date('now','localtime')"
  ).get();
  return {
    total: total.cnt,
    used: used.cnt,
    available: available.cnt,
    today_used: todayUsed.cnt
  };
}

function getAvailableCode() {
  return db.prepare("SELECT * FROM codes WHERE status = 'available' ORDER BY id ASC LIMIT 1").get();
}

// 原子抢占：事务内 SELECT + UPDATE，保证并发安全
function claimCode(ip, ua) {
  const claim = db.transaction(() => {
    const row = db.prepare(
      "SELECT * FROM codes WHERE status = 'available' ORDER BY id ASC LIMIT 1"
    ).get();
    if (!row) return null;
    
    db.prepare(
      "UPDATE codes SET status = 'used', used_at = datetime('now','localtime'), access_ip = ?, user_agent = ? WHERE id = ?"
    ).run(ip, ua, row.id);
    
    row.status = 'used';
    return row;
  });
  return claim();
}

function getCodeById(id) {
  return db.prepare('SELECT * FROM codes WHERE id = ?').get(id);
}

function useCode(id, ip, ua) {
  const result = db.prepare(
    "UPDATE codes SET status = 'used', used_at = datetime('now','localtime'), access_ip = ?, user_agent = ? WHERE id = ? AND status = 'available'"
  ).run(ip, ua, id);
  return result.changes > 0;
}

function insertCodes(urls) {
  let inserted = 0;
  let skipped = 0;
  const checkStmt = db.prepare('SELECT COUNT(*) AS cnt FROM codes WHERE apple_url = ?');
  const insertStmt = db.prepare('INSERT INTO codes (apple_url) VALUES (?)');

  const tx = db.transaction((items) => {
    for (const url of items) {
      const trimmed = url.trim();
      if (!trimmed) continue;
      const exists = checkStmt.get(trimmed);
      if (exists.cnt > 0) {
        skipped++;
      } else {
        insertStmt.run(trimmed);
        inserted++;
      }
    }
  });

  tx(urls);
  return { inserted, skipped };
}

function getCodesPage(page, pageSize, statusFilter) {
  const offset = (page - 1) * pageSize;
  let whereClause = '';
  const params = [];
  if (statusFilter && statusFilter !== 'all') {
    whereClause = 'WHERE status = ?';
    params.push(statusFilter);
  }
  const countResult = db.prepare(`SELECT COUNT(*) AS cnt FROM codes ${whereClause}`).get(...params);
  const total = countResult.cnt;
  const rows = db.prepare(
    `SELECT * FROM codes ${whereClause} ORDER BY id DESC LIMIT ? OFFSET ?`
  ).all(...params, pageSize, offset);
  return { rows, total, page, pageSize, totalPages: Math.ceil(total / pageSize) };
}

function getLogsPage(page, pageSize) {
  const offset = (page - 1) * pageSize;
  const total = db.prepare("SELECT COUNT(*) AS cnt FROM codes WHERE status = 'used'").get().cnt;
  const rows = db.prepare(
    "SELECT * FROM codes WHERE status = 'used' ORDER BY used_at DESC LIMIT ? OFFSET ?"
  ).all(pageSize, offset);
  return { rows, total, page, pageSize, totalPages: Math.ceil(total / pageSize) };
}

function getWeekTrend() {
  const rows = db.prepare(`
    SELECT date(used_at) AS day, COUNT(*) AS cnt
    FROM codes
    WHERE status = 'used' AND used_at >= datetime('now', '-6 days', 'localtime')
    GROUP BY date(used_at)
    ORDER BY day ASC
  `).all();
  const days = [];
  const counts = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const dateStr = d.toISOString().slice(0, 10);
    days.push(dateStr);
    const found = rows.find(r => r.day === dateStr);
    counts.push(found ? found.cnt : 0);
  }
  return { days, counts };
}

function getMaxId() {
  const result = db.prepare('SELECT MAX(id) AS maxId FROM codes').get();
  return result.maxId || 0;
}

module.exports = {
  db,
  getStats,
  getAvailableCode,
  claimCode,
  getCodeById,
  useCode,
  insertCodes,
  getCodesPage,
  getLogsPage,
  getWeekTrend,
  getMaxId
};
