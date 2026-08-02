#!/bin/bash
# ===========================================================
# OA新闻代理 一键部署脚本
# 目标环境：银河麒麟 V10 / CentOS 7+ / RHEL 7+
# 部署到接入机（Nginx所在机器）
# ===========================================================

set -e

INSTALL_DIR="/opt/oa-news-proxy"
LOG_DIR="/var/log/oa-proxy"
NGINX_CONF="/etc/nginx/conf.d/oa-news-proxy.conf"
DEPLOY_ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "============================================"
echo " OA新闻代理 一键部署"
echo " 时间：$(date '+%Y-%m-%d %H:%M:%S')"
echo " 部署源：${DEPLOY_ROOT}"
echo "============================================"

# ─── 1. 环境检查 ────────────────────────────────
echo ""
echo "[1/7] 环境检查..."

check_cmd() {
    if command -v "$1" >/dev/null 2>&1; then
        echo "  ✅ $1: $(command -v $1)"
        return 0
    else
        echo "  ❌ $1 未安装"
        return 1
    fi
}

check_cmd nginx || { echo "错误：Nginx未安装，请先安装Nginx"; exit 1; }
check_cmd python3 || { echo "错误：Python3未安装，请先安装Python3"; exit 1; }
check_cmd curl || { echo "错误：curl未安装，请先安装curl"; exit 1; }

# 检查 Python requests 库
python3 -c "import requests" 2>/dev/null && echo "  ✅ python3-requests 已安装" || {
    echo "  ⚠️  python3-requests 未安装，正在安装..."
    if command -v pip3 >/dev/null 2>&1; then
        pip3 install requests
    elif command -v yum >/dev/null 2>&1; then
        yum install -y python3-requests
    elif command -v apt-get >/dev/null 2>&1; then
        apt-get install -y python3-requests
    else
        echo "  ❌ 无法自动安装 python3-requests，请手动执行: pip3 install requests"
        exit 1
    fi
    echo "  ✅ python3-requests 安装完成"
}

# ─── 2. 创建目录 ──────────────────────────────────
echo ""
echo "[2/7] 创建安装目录..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$LOG_DIR"
echo "  ✅ $INSTALL_DIR"
echo "  ✅ $LOG_DIR"

# ─── 3. 部署文件 ──────────────────────────────────
echo ""
echo "[3/7] 部署代理服务文件..."

cp "${DEPLOY_ROOT}/scripts/oa_proxy.py"   "${INSTALL_DIR}/oa_proxy.py"
cp "${DEPLOY_ROOT}/scripts/oa_config.json" "${INSTALL_DIR}/oa_config.json"
cp "${DEPLOY_ROOT}/scripts/verify.sh"     "${INSTALL_DIR}/verify.sh"

chmod +x "${INSTALL_DIR}/oa_proxy.py"
chmod +x "${INSTALL_DIR}/verify.sh"

# 配置文件权限（包含密码，仅root可读）
chmod 600 "${INSTALL_DIR}/oa_config.json"

echo "  ✅ 代理脚本已部署到 ${INSTALL_DIR}/"

# ─── 4. 部署 Nginx 配置 ────────────────────────────
echo ""
echo "[4/7] 部署 Nginx 代理配置..."

# 备份原配置
if [ -f "$NGINX_CONF" ]; then
    cp "$NGINX_CONF" "${NGINX_CONF}.bak.$(date +%Y%m%d%H%M%S)"
    echo "  ✅ 已备份原配置"
fi

cp "${DEPLOY_ROOT}/nginx/oa-news-proxy.conf" "$NGINX_CONF"
echo "  ✅ Nginx配置已部署到 ${NGINX_CONF}"

# 检查Nginx配置语法
if nginx -t 2>/dev/null; then
    echo "  ✅ Nginx配置语法检查通过"
    nginx -s reload 2>/dev/null || systemctl reload nginx 2>/dev/null || true
    echo "  ✅ Nginx已重载"
else
    echo "  ⚠️  Nginx配置语法有误，请检查是否缺少include指令"
    echo "     可能需要在主nginx.conf中添加: include /etc/nginx/conf.d/*.conf;"
fi

# ─── 5. 部署 systemd 服务 ─────────────────────────
echo ""
echo "[5/7] 注册 systemd 服务..."

cp "${DEPLOY_ROOT}/scripts/oa-proxy.service" /etc/systemd/system/oa-proxy.service
systemctl daemon-reload
echo "  ✅ oa-proxy.service 已注册"

# ─── 6. 提示配置 ─────────────────────────────────
echo ""
echo "[6/7] 配置提醒..."
echo "  ┌─────────────────────────────────────────────────────┐"
echo "  │ 请在启动服务前编辑配置文件：                          │"
echo "  │                                                     │"
echo "  │   vi ${INSTALL_DIR}/oa_config.json  │"
echo "  │                                                     │"
echo "  │ 必须修改：                                           │"
echo "  │   credentials.username  → OA服务账号                  │"
echo "  │   credentials.password  → OA密码                     │"
echo "  │                                                     │"
echo "  │ 可选修改：                                           │"
echo "  │   oa.base_url           → OA地址（默认已配好）        │"
echo "  │   oa.auth_type          → 认证方式                   │"
echo "  │     cookie_form: 表单登录（默认，SharePoint FBA）      │"
echo "  │     ntlm: Windows集成认证（需额外安装requests_ntlm）  │"
echo "  └─────────────────────────────────────────────────────┘"
echo ""

# ─── 7. 启动服务 ─────────────────────────────────
read -p "是否现在启动服务？(y/N): " answer
if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
    echo ""
    echo "[7/7] 启动 oa-proxy 服务..."
    systemctl start oa-proxy
    systemctl enable oa-proxy

    sleep 2
    if systemctl is-active --quiet oa-proxy; then
        echo "  ✅ oa-proxy 服务已启动并设为开机自启"
        echo ""
        echo "  查看日志：journalctl -u oa-proxy -f"
        echo "  运行验证：bash ${INSTALL_DIR}/verify.sh"
    else
        echo "  ❌ 服务启动失败，请查看日志："
        echo "     journalctl -u oa-proxy -n 50"
    fi
else
    echo ""
    echo "  跳过启动。配置好后手动执行："
    echo "    systemctl start oa-proxy"
    echo "    systemctl enable oa-proxy"
fi

echo ""
echo "============================================"
echo " 部署完成！"
echo "============================================"
echo ""
echo " 后续步骤："
echo " 1. 编辑配置：vi ${INSTALL_DIR}/oa_config.json"
echo " 2. 启动服务：systemctl start oa-proxy"
echo " 3. 验证部署：bash ${INSTALL_DIR}/verify.sh"
echo ""
echo " 服务管理："
echo "   systemctl start   oa-proxy   # 启动"
echo "   systemctl stop    oa-proxy   # 停止"
echo "   systemctl restart oa-proxy   # 重启"
echo "   systemctl status  oa-proxy   # 状态"
echo "   journalctl -u oa-proxy -f    # 实时日志"
echo ""
