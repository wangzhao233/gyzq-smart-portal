#!/bin/bash
# ===========================================================
# OA新闻代理 Java版 — 一键部署脚本
# 目标环境：银河麒麟 V10 / CentOS 7+ / RHEL 7+
# ===========================================================

set -e

INSTALL_DIR="/opt/oa-news-proxy"
LOG_DIR="/var/log/oa-proxy"
NGINX_CONF="/etc/nginx/conf.d/oa-news-proxy.conf"
DEPLOY_ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "============================================"
echo " OA新闻代理 一键部署（Java版）"
echo " 时间：$(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"

# ─── 1. 环境检查 ────────────────────────────────
echo ""
echo "[1/7] 环境检查..."

check_cmd() {
    command -v "$1" >/dev/null 2>&1 && echo "  ✅ $1: $($1 -version 2>&1 | head -1)" || echo "  ❌ $1 未安装"
}

check_cmd java
check_cmd javac
check_cmd nginx
check_cmd curl

if ! command -v java >/dev/null 2>&1; then
    echo "错误：JDK未安装"
    echo "银河麒麟安装：yum install java-1.8.0-openjdk-devel"
    echo "或：yum install java-11-openjdk-devel"
    exit 1
fi
if ! command -v nginx >/dev/null 2>&1; then
    echo "错误：Nginx未安装"
    exit 1
fi

# ─── 2. 编译 ─────────────────────────────────
echo ""
echo "[2/7] 编译Java源码..."
mkdir -p "${DEPLOY_ROOT}/build/classes"
javac -encoding UTF-8 -d "${DEPLOY_ROOT}/build/classes" \
    "${DEPLOY_ROOT}/src/OaProxyServer.java"
echo "  ✅ 编译成功"

# ─── 3. 打包JAR ──────────────────────────────
echo ""
echo "[3/7] 打包JAR..."
mkdir -p "${DEPLOY_ROOT}/build/META-INF"
cat > "${DEPLOY_ROOT}/build/META-INF/MANIFEST.MF" << 'EOF'
Manifest-Version: 1.0
Main-Class: src.OaProxyServer
EOF

cd "${DEPLOY_ROOT}/build"
jar cfm oa-proxy.jar META-INF/MANIFEST.MF -C classes .
cd "${DEPLOY_ROOT}"
echo "  ✅ oa-proxy.jar 打包完成"

# ─── 4. 部署 ─────────────────────────────────
echo ""
echo "[4/7] 部署到 ${INSTALL_DIR}..."
mkdir -p "$INSTALL_DIR" "$LOG_DIR"

cp "${DEPLOY_ROOT}/build/oa-proxy.jar" "${INSTALL_DIR}/oa-proxy.jar"
cp "${DEPLOY_ROOT}/oa-proxy.properties" "${INSTALL_DIR}/oa-proxy.properties"
cp "${DEPLOY_ROOT}/verify.sh" "${INSTALL_DIR}/verify.sh" 2>/dev/null || true
cp "${DEPLOY_ROOT}/nginx/oa-news-proxy.conf" "$NGINX_CONF"

chmod 600 "${INSTALL_DIR}/oa-proxy.properties"
chmod +x "${INSTALL_DIR}/verify.sh" 2>/dev/null || true
rm -rf "${DEPLOY_ROOT}/build"

echo "  ✅ 部署完成"

# ─── 5. Nginx ────────────────────────────────
echo ""
echo "[5/7] 配置Nginx..."
if nginx -t 2>/dev/null; then
    nginx -s reload 2>/dev/null || systemctl reload nginx 2>/dev/null || true
    echo "  ✅ Nginx配置已重载"
else
    echo "  ⚠️  Nginx配置有误，请检查"
fi

# ─── 6. systemd ──────────────────────────────
echo ""
echo "[6/7] 注册systemd服务..."
cat > /etc/systemd/system/oa-proxy.service << UNIT
[Unit]
Description=OA News Proxy (Java) - SharePoint新闻数据代理
After=network.target nginx.service

[Service]
Type=simple
WorkingDirectory=/opt/oa-news-proxy
ExecStart=/usr/bin/java -Xms64m -Xmx256m -jar /opt/oa-news-proxy/oa-proxy.jar /opt/oa-news-proxy/oa-proxy.properties
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=oa-proxy
Environment=LANG=zh_CN.UTF-8

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
echo "  ✅ oa-proxy.service 已注册"

# ─── 7. 启动提示 ─────────────────────────────
echo ""
echo "[7/7] 部署完成！"
echo ""
echo "  ┌───────────────────────────────────────────────────────┐"
echo "  │ 请先编辑配置文件（填入OA账号密码）：                    │"
echo "  │                                                       │"
echo "  │   vi ${INSTALL_DIR}/oa-proxy.properties               │"
echo "  │                                                       │"
echo "  │ 然后启动服务：                                         │"
echo "  │   systemctl start oa-proxy                            │"
echo "  │   systemctl enable oa-proxy                           │"
echo "  │                                                       │"
echo "  │ 验证部署：                                             │"
echo "  │   bash ${INSTALL_DIR}/verify.sh                       │"
echo "  └───────────────────────────────────────────────────────┘"
echo ""
