#!/bin/bash
# ============================================================
# 国元元信 · 统一下载门户 v1.0 — 一键部署脚本
# 目标服务器：门户应用服务器或独立服务器
# 用法：sudo bash deploy.sh
# ============================================================
set -e

APP_DIR="/opt/download-portal"
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"
NODE_USER="${NODE_USER:-root}"

echo "============================================"
echo " 国元元信统一下载门户 v1.0 部署"
echo " 时间：$(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
echo ""

# ─── 1. 环境检查 ────────────────────────────
echo "[1/6] 环境检查..."
command -v node >/dev/null 2>&1 || { echo "❌ Node.js 未安装，请先安装 Node 18+"; exit 1; }
echo "  ✅ Node $(node -v)"

# ─── 2. 部署文件 ────────────────────────────
echo "[2/6] 部署文件到 ${APP_DIR}..."
mkdir -p "${APP_DIR}"
cp -r "${SOURCE_DIR}/server.js" \
      "${SOURCE_DIR}/db.js" \
      "${SOURCE_DIR}/admin" \
      "${SOURCE_DIR}/views" \
      "${SOURCE_DIR}/public" \
      "${SOURCE_DIR}/scripts" \
      "${SOURCE_DIR}/package.json" \
      "${SOURCE_DIR}/package-lock.json" \
      "${APP_DIR}/"

# 生产配置
if [ ! -f "${APP_DIR}/.env" ]; then
  cp "${SOURCE_DIR}/.env.production" "${APP_DIR}/.env"
  echo "  ⚠️  请编辑 ${APP_DIR}/.env 修改密码和域名"
else
  echo "  .env 已存在，跳过"
fi

mkdir -p "${APP_DIR}/data"
echo "  ✅ 文件部署完成"

# ─── 3. 安装依赖 ────────────────────────────
echo "[3/6] 安装依赖..."
cd "${APP_DIR}"
npm install --omit=dev 2>&1 | tail -1
echo "  ✅ 依赖安装完成"

# ─── 4. 初始化数据库 ────────────────────────
echo "[4/6] 初始化数据库..."
node scripts/init-db.js 2>/dev/null || echo "  DB 已存在，跳过"
echo "  ✅ 数据库就绪"

# ─── 5. systemd 服务 ────────────────────────
echo "[5/6] 注册 systemd 服务..."
cat > /etc/systemd/system/download-portal.service << UNIT
[Unit]
Description=国元元信统一下载门户 v1.0
After=network.target

[Service]
Type=simple
User=${NODE_USER}
WorkingDirectory=${APP_DIR}
ExecStart=/usr/bin/node ${APP_DIR}/server.js
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable download-portal.service
systemctl restart download-portal.service
echo "  ✅ 服务已启动"

# ─── 6. Nginx（可选）─────────────────────────
if command -v nginx &>/dev/null; then
  echo "[6/6] 配置 Nginx..."
  cat > /etc/nginx/conf.d/download-portal.conf << 'NGINX'
server {
    listen 443 ssl;
    server_name download.oa.gyzq.com;

    location / {
        proxy_pass http://127.0.0.1:3100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX
  nginx -t && systemctl reload nginx
  echo "  ✅ Nginx 配置完成"
else
  echo "[6/6] Nginx 未安装，跳过"
fi

echo ""
echo "============================================"
echo " 部署完成！"
echo ""
echo " 本地访问: http://localhost:3100"
echo " 管理后台: http://localhost:3100/admin"
echo " 查看日志: journalctl -u download-portal -f"
echo ""
echo " ⚠️  部署后操作："
echo "   1. 编辑 ${APP_DIR}/.env 设置域名和密码"
echo "   2. 管理后台导入真实兑换链接"
echo "   3. systemctl restart download-portal"
echo "============================================"
