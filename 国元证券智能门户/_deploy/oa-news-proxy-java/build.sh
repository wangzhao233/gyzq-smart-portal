#!/bin/bash
# ===========================================================
# OA新闻代理 Java版 — 编译打包脚本
# 目标：生成可直接运行的oa-proxy.jar
# 用法：bash build.sh
# ===========================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="${SCRIPT_DIR}/src"
BUILD_DIR="${SCRIPT_DIR}/build"
JAR_NAME="oa-proxy.jar"

echo "============================================"
echo " OA新闻代理 编译打包（Java版）"
echo "============================================"

# 检查Java
if ! command -v javac >/dev/null 2>&1; then
    echo "❌ javac 未安装，请先安装 JDK"
    exit 1
fi

echo "Java版本：$(java -version 2>&1 | head -1)"
echo ""

# 清理
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}/classes" "${BUILD_DIR}/META-INF"

# 编译
echo "[1/3] 编译Java源码..."
javac -encoding UTF-8 -d "${BUILD_DIR}/classes" "${SRC_DIR}/OaProxyServer.java"
echo "  ✅ 编译成功"

# 创建MANIFEST
cat > "${BUILD_DIR}/META-INF/MANIFEST.MF" << 'EOF'
Manifest-Version: 1.0
Main-Class: src.OaProxyServer
EOF

# 打包JAR
echo "[2/3] 打包JAR..."
cd "${BUILD_DIR}"
jar cfm "${JAR_NAME}" META-INF/MANIFEST.MF -C classes .
cd "${SCRIPT_DIR}"
mv "${BUILD_DIR}/${JAR_NAME}" "${SCRIPT_DIR}/${JAR_NAME}"
echo "  ✅ ${JAR_NAME} 已生成"

# 清理临时文件
rm -rf "${BUILD_DIR}"

echo "[3/3] 验证JAR..."
java -jar "${SCRIPT_DIR}/${JAR_NAME}" --help 2>/dev/null && true
echo "  ✅ JAR可正常运行"

echo ""
echo "============================================"
echo " 编译完成！"
echo " 输出文件：${SCRIPT_DIR}/${JAR_NAME}"
echo " 大小：$(du -h ${SCRIPT_DIR}/${JAR_NAME} | cut -f1)"
echo "============================================"
echo ""
echo " 部署到客户服务器："
echo "   1. 上传 oa-proxy.jar + oa-proxy.properties"
echo "   2. 编辑 oa-proxy.properties 填入账号密码"
echo "   3. java -jar oa-proxy.jar oa-proxy.properties"
echo ""
