require('dotenv').config();
const express = require('express');
const path = require('path');
const basicAuth = require('express-basic-auth');
const QRCode = require('qrcode');
const db = require('./db');

const app = express();
const PORT = process.env.PORT || 3100;
const BASE_URL = process.env.BASE_URL || 'http://localhost:3100';
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'admin123';

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

// ─── 浏览器检测 ──────────────────────────
function isInAppBrowser(ua) {
  return /MicroMessenger|wxwork/i.test(ua);
}
function isIOS(ua) {
  return /iPhone|iPad|iPod/i.test(ua);
}

function browserGuard(req, res, next) {
  const ua = req.headers['user-agent'] || '';
  if (isInAppBrowser(ua)) {
    return res.render('browser-guide', { isIOS: isIOS(ua) });
  }
  next();
}

// ─── 用户页面路由 ────────────────────────
// F3: 统一下载首页
app.get('/', browserGuard, (req, res) => {
  res.render('index');
});

// F1: iOS ABM 下载页（QR → /r/claim 原子抢占）
app.get('/ios', browserGuard, async (req, res) => {
  try {
    const stats = db.getStats();
    let qrDataUrl = null;
    if (stats.available > 0) {
      qrDataUrl = await QRCode.toDataURL(`${BASE_URL}/r/claim`, { width: 200, margin: 2 });
    }
    res.render('ios', { qrDataUrl, remaining: stats.available, codeId: null });
  } catch (err) {
    console.error('iOS page error:', err);
    res.status(500).send('服务器内部错误');
  }
});

// Android 下载页（QR → 云端下载）
app.get('/android', browserGuard, async (req, res) => {
  const cloudUrl = 'https://work.weixin.qq.com/ld/8rS-83SmwJ9nzjsxuODkk7FiQ20uz1TAosvqc31scPs';
  const qrDataUrl = await QRCode.toDataURL(cloudUrl, { width: 200, margin: 2 });
  res.render('android', { qrDataUrl });
});

// 原子抢占：扫码时分配下一个可用码（并发安全）
app.get('/r/claim', (req, res) => {
  const ip = req.ip || req.connection.remoteAddress;
  const ua = req.headers['user-agent'] || '';
  const code = db.claimCode(ip, ua);
  if (!code) {
    return res.status(410).render('error', { message: '兑换码已用完，请联系管理员补充' });
  }
  res.redirect(302, code.apple_url);
});

// F2: 兑换跳转（兼容旧链接 /r/:id）
app.get('/r/:id', (req, res) => {
  const id = parseInt(req.params.id);
  if (isNaN(id)) return res.status(400).render('error', { message: '无效的兑换链接' });
  const code = db.getCodeById(id);
  if (!code) return res.status(404).render('error', { message: '兑换链接不存在' });
  if (code.status !== 'available') return res.status(410).render('error', { message: '此兑换码已被使用' });

  const ip = req.ip || req.connection.remoteAddress;
  const ua = req.headers['user-agent'] || '';
  db.useCode(id, ip, ua);
  res.redirect(302, code.apple_url);
});

// ─── API ────────────────────────────────
app.get('/api/stats', (req, res) => {
  res.json(db.getStats());
});

app.get('/api/code/current', (req, res) => {
  const stats = db.getStats();
  res.json({ remaining: stats.available });
});

// ─── 管理后台（HTTP Basic Auth）──────────
const adminAuth = basicAuth({
  users: { admin: ADMIN_PASSWORD },
  challenge: true,
  realm: 'Admin Panel'
});
app.use('/admin', adminAuth, require('./admin/admin'));

// ─── 启动 ───────────────────────────────
app.listen(PORT, () => {
  console.log(`下载门户 v1.1 已启动: http://localhost:${PORT}`);
  console.log(`管理后台: http://localhost:${PORT}/admin`);
});
