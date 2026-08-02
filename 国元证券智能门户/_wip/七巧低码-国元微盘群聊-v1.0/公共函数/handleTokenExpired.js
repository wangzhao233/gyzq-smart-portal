// ===== 公共函数：处理token过期 =====
// 用途：当API返回 errcode=42001 时统一处理
// 位置：复制到每个脚本的顶部

function handleTokenExpired(errCode, refreshFn) {
    if (errCode == 42001 || errCode == "42001") {
        $.log.warn("access_token已过期，重新获取...");
        return refreshFn();
    }
    return null;
}
