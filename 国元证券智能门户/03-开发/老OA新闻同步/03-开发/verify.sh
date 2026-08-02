#!/bin/bash
# ===========================================================
# OA新闻代理验证脚本
# 用法：bash verify.sh [域名]
# 默认域名：portal.oa.gyzq.com
# ===========================================================

DOMAIN="${1:-portal.oa.gyzq.com}"
BASE="https://${DOMAIN}"
PASS=0
FAIL=0
WARN=0
SLOW_THRESHOLD=5  # 秒

echo "============================================"
echo " OA新闻代理部署验证"
echo " 门户域名：${DOMAIN}"
echo " 时间：$(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
echo ""

# --- 1. 系统服务检查 ---
echo "[1/5] 检查 oa-proxy 服务状态..."
if systemctl is-active --quiet oa-proxy 2>/dev/null; then
    echo "  ✅ oa-proxy 服务运行中"
    PASS=$((PASS+1))
else
    echo "  ❌ oa-proxy 服务未运行"
    echo "     执行: systemctl start oa-proxy"
    echo "     查看: journalctl -u oa-proxy -n 20"
    FAIL=$((FAIL+1))
fi

# --- 2. 本地代理端口检查 ---
echo ""
echo "[2/5] 检查本地代理端口 8899..."
if curl -s --connect-timeout 2 http://127.0.0.1:8899/oa-news/gsdt/_api/web/title >/dev/null 2>&1; then
    echo "  ✅ 本地代理端口可达"
    PASS=$((PASS+1))
elif curl -s --connect-timeout 2 http://127.0.0.1:8899/ >/dev/null 2>&1; then
    echo "  ⚠️  端口可达但API返回异常（可能OA未登录）"
    WARN=$((WARN+1))
else
    echo "  ❌ 本地代理端口不可达"
    echo "     确认: netstat -tlnp | grep 8899"
    FAIL=$((FAIL+1))
fi

# --- 3. Nginx代理检查 ---
echo ""
echo "[3/5] 检查 Nginx 代理配置..."
if nginx -t 2>/dev/null; then
    echo "  ✅ Nginx 配置语法正确"
    PASS=$((PASS+1))
else
    echo "  ❌ Nginx 配置有误，请检查 /etc/nginx/conf.d/oa-news-proxy.conf"
    FAIL=$((FAIL+1))
fi

# --- 4. API接口连通性检查 ---
echo ""
echo "[4/5] 逐个检查新闻分类接口..."

declare -A CATEGORIES=(
    ["公司动态"]="/oa-news/gsdt/_api/lists/getbytitle('页面')/items?\$top=1"
    ["部门简报"]="/oa-news/bmjb/_api/lists/getbytitle('页面')/items?\$top=1"
    ["创新发展"]="/oa-news/cxfz/zcdt/_api/lists/getbytitle('页面')/items?\$top=1"
    ["监管动态"]="/oa-news/hggl/jgdt/_api/lists/getbytitle('页面')/items?\$top=1"
    ["党建群团"]="/oa-news/djqt/_api/lists/getbytitle('页面')/items?\$top=1"
    ["子公司及分支机构"]="/oa-news/zgs/_api/lists/getbytitle('页面')/items?\$top=1"
    ["党建指南"]="/oa-news/lxyz/_api/lists/getbytitle('页面')/items?\$top=1"
)

for category in "${!CATEGORIES[@]}"; do
    url="${BASE}${CATEGORIES[$category]}"
    start_time=$(date +%s%N)

    resp=$(curl -s -w "\n%{http_code}|%{time_total}" \
        --connect-timeout 5 --max-time 15 \
        "$url" 2>/dev/null)

    http_code=$(echo "$resp" | tail -1 | cut -d'|' -f1)
    time_total=$(echo "$resp" | tail -1 | cut -d'|' -f2)

    # 检查JSON是否包含Title字段
    has_title=$(echo "$resp" | head -n -1 | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    titles = [item.get('Title','') for item in data.get('d',{}).get('results',[])]
    print(len(titles))
except: print(0)
" 2>/dev/null)

    if [ "$http_code" = "200" ] && [ "${has_title:-0}" -gt 0 ]; then
        echo "  ✅ ${category}：HTTP ${http_code}，返回 ${has_title} 条，耗时 ${time_total}s"
        PASS=$((PASS+1))
    elif [ "$http_code" = "200" ]; then
        echo "  ⚠️  ${category}：HTTP ${http_code}，但JSON解析异常，耗时 ${time_total}s"
        WARN=$((WARN+1))
    elif [ "$http_code" = "401" ]; then
        echo "  ❌ ${category}：HTTP 401（Cookie已过期，请重启服务或检查账号）"
        FAIL=$((FAIL+1))
    elif [ "$http_code" = "502" ] || [ "$http_code" = "503" ]; then
        echo "  ❌ ${category}：HTTP ${http_code}（代理服务不可用）"
        FAIL=$((FAIL+1))
    else
        echo "  ⚠️  ${category}：HTTP ${http_code}，耗时 ${time_total}s"
        WARN=$((WARN+1))
    fi
done

# --- 5. 门户前端访问检查 ---
echo ""
echo "[5/5] 检查门户前端页面..."
portal_status=$(curl -s -o /dev/null -w "%{http_code}" \
    --connect-timeout 5 --max-time 10 "${BASE}/" 2>/dev/null)
if [ "$portal_status" = "200" ] || [ "$portal_status" = "301" ] || [ "$portal_status" = "302" ]; then
    echo "  ✅ 门户页面可访问（HTTP ${portal_status}）"
    PASS=$((PASS+1))
else
    echo "  ⚠️  门户页面返回 HTTP ${portal_status}（可能受网络环境限制）"
    WARN=$((WARN+1))
fi

# --- 汇总 ---
echo ""
echo "============================================"
echo " 验证结果汇总"
echo "============================================"
echo "  ✅ 通过：${PASS}"
echo "  ⚠️  警告：${WARN}"
echo "  ❌ 失败：${FAIL}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "  🎉 所有关键检查通过！OA新闻代理部署成功。"
    echo ""
    echo "  门户数据源URL示例（公司动态）："
    echo "  ${BASE}/oa-news/gsdt/_api/lists/getbytitle('页面')/items?\$select=Created,Title,Id,ArticleStartDate,FileRef,Modified&\$top=20&\$orderby=ArticleStartDate%20desc&\$filter=OData__ModerationStatus%20eq%200"
    exit 0
else
    echo "  有 ${FAIL} 项检查失败，请修复后重新验证。"
    exit 1
fi
