const express = require('express');
const router = express.Router();
const db = require('../db');

// F4: 管理后台仪表盘 (GET /admin)
router.get('/', (req, res) => {
  const stats = db.getStats();
  const trend = db.getWeekTrend();
  res.render('admin', {
    stats,
    trend: JSON.stringify(trend),
    tab: 'dashboard',
    pool: null,
    logs: null,
    statusFilter: 'all',
    message: null
  });
});

// F4: 批量导入兑换码 (POST /admin/upload)
router.post('/upload', (req, res) => {
  const stats = db.getStats();
  const trend = db.getWeekTrend();
  const raw = req.body.codes || '';
  const urls = raw.split('\n').map(s => s.trim()).filter(s => s.length > 0);
  if (urls.length === 0) {
    return res.render('admin', {
      stats,
      trend: JSON.stringify(trend),
      tab: 'import',
      pool: null,
      logs: null,
      statusFilter: 'all',
      message: { type: 'error', text: '请粘贴至少一条兑换链接' }
    });
  }
  const result = db.insertCodes(urls);
  res.render('admin', {
    stats: db.getStats(),
    trend: JSON.stringify(trend),
    tab: 'import',
    pool: null,
    logs: null,
    statusFilter: 'all',
    message: { type: 'success', text: `导入成功：${result.inserted} 条，跳过重复：${result.skipped} 条` }
  });
});

// F4: 链接池 Tab (GET /admin/pool)
router.get('/pool', (req, res) => {
  const stats = db.getStats();
  const trend = db.getWeekTrend();
  const page = parseInt(req.query.page) || 1;
  const pageSize = 50;
  const statusFilter = req.query.status || 'all';
  const data = db.getCodesPage(page, pageSize, statusFilter);
  res.render('admin', {
    stats,
    trend: JSON.stringify(trend),
    tab: 'pool',
    pool: data,
    logs: null,
    statusFilter,
    message: null
  });
});

// F4: 消耗日志 Tab (GET /admin/logs)
router.get('/logs', (req, res) => {
  const stats = db.getStats();
  const trend = JSON.stringify(db.getWeekTrend());
  const page = parseInt(req.query.page) || 1;
  const pageSize = 20;
  const data = db.getLogsPage(page, pageSize);
  res.render('admin', {
    stats,
    trend,
    tab: 'logs',
    pool: null,
    logs: data,
    statusFilter: 'all',
    message: null
  });
});

module.exports = router;
