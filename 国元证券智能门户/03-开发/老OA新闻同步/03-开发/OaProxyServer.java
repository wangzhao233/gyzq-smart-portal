package src;

import com.sun.net.httpserver.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicReference;
import java.util.logging.*;
import java.util.regex.*;

/**
 * OA新闻代理服务 V2.0 — 零外部依赖纯Java版
 * 支持智能门户主动拉取模式：
 *   - 接收门户POST请求 → 调用SharePoint REST API → 转换OData JSON为门户消息列表格式
 * 编译：javac -encoding UTF-8 src/OaProxyServer.java
 * 运行：java -cp . src.OaProxyServer [--test-mode] [config.properties路径]
 *
 * @author 王昭 (道一云)
 * @since 2026-07-16
 * @version 2.2 2026-07-23 修复登录+内容字段+URL编码+日期+escapeJson
 */
public class OaProxyServer {

    static final String DEFAULT_CONFIG = "oa-proxy.properties";
    static Properties config = new Properties();
    static String OA_BASE;
    static int LISTEN_PORT;
    static String USERNAME;
    static String PASSWORD;
    static String AUTH_TYPE;
    static long COOKIE_MAX_AGE_MS;
    static int REQUEST_TIMEOUT;
    static int RETRY_COUNT;
    static long START_TIME = System.currentTimeMillis();
    static boolean testMode = false;

    static final Logger log = Logger.getLogger("oa-proxy");
    static final CookieManager cookieManager = new CookieManager(null, CookiePolicy.ACCEPT_ALL);
    static final AtomicReference<Date> lastLogin = new AtomicReference<>();
    static final ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(2);

    // typeId → SP站点路径映射
    static final Map<String, String> TYPE_PATH_MAP = new LinkedHashMap<>();
    static final Map<String, String> TYPE_NAME_MAP = new LinkedHashMap<>();
    static {
        TYPE_PATH_MAP.put("gsdt", "/gsdt/");           TYPE_NAME_MAP.put("gsdt", "公司动态");
        TYPE_PATH_MAP.put("bmjb", "/bmjb/");           TYPE_NAME_MAP.put("bmjb", "部门简报");
        TYPE_PATH_MAP.put("cxfz", "/cxfz/zcdt/");      TYPE_NAME_MAP.put("cxfz", "创新发展");
        TYPE_PATH_MAP.put("jgdt", "/hggl/jgdt/");      TYPE_NAME_MAP.put("jgdt", "监管动态");
        TYPE_PATH_MAP.put("djqt", "/gsdt/djqt/");      TYPE_NAME_MAP.put("djqt", "党建群团");
        TYPE_PATH_MAP.put("zgs",  "/gsdt/zgsfzjg/");   TYPE_NAME_MAP.put("zgs",  "子公司及分支机构");
        TYPE_PATH_MAP.put("lxyz", "/jdlm/lxyz/");      TYPE_NAME_MAP.put("lxyz", "党建指南");
    }

    public static void main(String[] args) throws Exception {
        // 解析 --test-mode 参数
        String configFile = null;
        for (String arg : args) {
            if ("--test-mode".equals(arg)) {
                testMode = true;
            } else {
                configFile = arg;
            }
        }
        if (configFile == null) configFile = DEFAULT_CONFIG;
        loadConfig(configFile);
        initLogger();

        if (testMode) {
            logInfo("🧪 测试模式已启用，跳过OA登录验证");
        } else {
            logInfo("启动前验证OA登录...");
            loginSharePoint();
            logInfo("OA登录验证通过 ✅");
        }

        HttpServer server = HttpServer.create(new InetSocketAddress(LISTEN_PORT), 0);
        server.createContext("/api/news", new NewsApiHandler());   // 门户主动拉取端点
        server.createContext("/health", new HealthHandler());       // 健康检查
        server.setExecutor(Executors.newFixedThreadPool(10));
        server.start();

        logInfo("=".repeat(60));
        logInfo("OA新闻代理服务 V2.0 启动");
        logInfo("监听地址: 0.0.0.0:" + LISTEN_PORT);
        logInfo("门户端点: POST /api/news");
        logInfo("OA目标:   " + OA_BASE);
        logInfo("=".repeat(60));

        if (testMode) {
            logInfo("🧪 测试模式：Cookie自动刷新已禁用");
        } else {
            scheduler.scheduleAtFixedRate(() -> {
                try { if (isCookieExpired()) { loginSharePoint(); logInfo("Cookie自动刷新成功"); } }
                catch (Exception e) { logSevere("Cookie刷新失败: " + e.getMessage()); }
            }, 30, 30, TimeUnit.MINUTES);
        }

        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            logInfo("服务正在关闭...");
            scheduler.shutdown();
            server.stop(2);
        }));
        Thread.currentThread().join();
    }

    // ─── 配置/日志 ─────────────────
    static void loadConfig(String path) throws IOException {
        File f = new File(path);
        if (!f.exists()) { System.err.println("配置文件不存在: " + f.getAbsolutePath()); System.exit(1); }
        try (InputStream in = new FileInputStream(f)) { config.load(in); }
        OA_BASE = config.getProperty("oa.base.url", "http://home.oa.gyzq.com").replaceAll("/$", "");
        LISTEN_PORT = Integer.parseInt(config.getProperty("proxy.listen.port", "8899"));
        USERNAME = config.getProperty("oa.username", "");
        PASSWORD = config.getProperty("oa.password", "");
        AUTH_TYPE = config.getProperty("oa.auth.type", "cookie_form");
        COOKIE_MAX_AGE_MS = Long.parseLong(config.getProperty("session.cookie.max.age.hours", "4")) * 3600000L;
        REQUEST_TIMEOUT = Integer.parseInt(config.getProperty("session.request.timeout.seconds", "15")) * 1000;
        RETRY_COUNT = Integer.parseInt(config.getProperty("session.retry.count", "3"));
        if (!testMode && (USERNAME.isEmpty() || PASSWORD.isEmpty())) { System.err.println("错误: 账号密码不能为空"); System.exit(1); }
    }

    static void initLogger() throws IOException {
        String logFile = config.getProperty("logging.file", "/var/log/oa-proxy/proxy.log");
        File logFileObj = new File(logFile);
        File parentDir = logFileObj.getParentFile();
        if (parentDir != null) parentDir.mkdirs();
        Logger root = Logger.getLogger("");
        root.setLevel(Level.INFO);
        for (Handler h : root.getHandlers()) root.removeHandler(h);
        FileHandler fh = new FileHandler(logFile, 10*1024*1024, 3, true);
        fh.setFormatter(new SimpleFormatter() {
            SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
            @Override public String format(LogRecord r) {
                return sdf.format(new Date(r.getMillis())) + " [" + r.getLevel() + "] " + r.getMessage() + "\n";
            }
        });
        root.addHandler(fh);
        ConsoleHandler ch = new ConsoleHandler(); ch.setFormatter(fh.getFormatter()); root.addHandler(ch);
    }
    static void logInfo(String msg)  { log.info(msg); }
    static void logSevere(String msg){ log.severe(msg); }

    // ─── SharePoint 认证 ─────────────
    static synchronized void loginSharePoint() throws Exception {
        cookieManager.getCookieStore().removeAll();
        for (int attempt = 1; attempt <= RETRY_COUNT; attempt++) {
            try {
                if ("ntlm".equalsIgnoreCase(AUTH_TYPE)) { loginNtlm(); } else { loginForm(); }
                lastLogin.set(new Date());
                String resp = httpGet(OA_BASE + "/gsdt/_api/web?$select=Title");
                if (resp.contains("\"Title\"")) {
                    logInfo("登录验证通过: " + extractTitle(resp));
                    return;
                }
                throw new RuntimeException("登录验证失败");
            } catch (Exception e) {
                if (attempt == RETRY_COUNT) throw e;
                Thread.sleep(RETRY_COUNT * 2000L);
            }
        }
    }

    static void loginForm() throws Exception {
        String loginUrl = OA_BASE + "/_forms/default.aspx?ReturnUrl=%2f";

        // 第一步：GET 登录页面，提取 ASP.NET 隐藏字段 + 会话 Cookie
        HttpURLConnection conn = openConnection(loginUrl, "GET");
        int getCode = conn.getResponseCode();
        String html = readStream(getCode >= 400 ? conn.getErrorStream() : conn.getInputStream());
        storeCookies(conn);
        conn.disconnect();

        String viewState          = extractHtmlHidden(html, "__VIEWSTATE");
        String viewStateGen       = extractHtmlHidden(html, "__VIEWSTATEGENERATOR");
        String eventValidation    = extractHtmlHidden(html, "__EVENTVALIDATION");
        String sideBySideToken    = extractHtmlHidden(html, "SideBySideToken");

        logInfo("[loginForm] GET 登录页 HTTP=" + getCode
            + " __VIEWSTATE=" + (viewState.isEmpty() ? "空" : "有值(" + viewState.length() + "字符)")
            + " __EVENTVALIDATION=" + (eventValidation.isEmpty() ? "空" : "有值")
            + " SideBySideToken=" + (sideBySideToken.isEmpty() ? "空" : "有值"));

        // 第二步：POST 提交所有表单字段（字段名小写 signInControl）
        String postData = "ctl00$PlaceHolderMain$signInControl$UserName=" + URLEncoder.encode(USERNAME, "UTF-8")
            + "&ctl00$PlaceHolderMain$signInControl$password=" + URLEncoder.encode(PASSWORD, "UTF-8")
            + "&ctl00$PlaceHolderMain$signInControl$login=" + URLEncoder.encode("登录", "UTF-8")
            + "&__VIEWSTATE=" + URLEncoder.encode(viewState, "UTF-8")
            + "&__VIEWSTATEGENERATOR=" + URLEncoder.encode(viewStateGen, "UTF-8")
            + "&__EVENTVALIDATION=" + URLEncoder.encode(eventValidation, "UTF-8")
            + "&SideBySideToken=" + URLEncoder.encode(sideBySideToken, "UTF-8");

        conn = openConnection(loginUrl, "POST");
        conn.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
        conn.setDoOutput(true);
        conn.setInstanceFollowRedirects(false);
        try (OutputStream os = conn.getOutputStream()) { os.write(postData.getBytes(StandardCharsets.UTF_8)); }

        int postCode = conn.getResponseCode();
        storeCookies(conn);
        conn.disconnect();

        logInfo("[loginForm] POST 响应: HTTP " + postCode);

        // 验证 FedAuth Cookie 是否获取成功
        boolean hasFedAuth = false;
        for (HttpCookie c : cookieManager.getCookieStore().getCookies()) {
            if ("FedAuth".equals(c.getName())) { hasFedAuth = true; break; }
        }
        if (!hasFedAuth) {
            throw new RuntimeException("登录失败: 未获取到 FedAuth cookie (HTTP " + postCode + ")");
        }
    }

    static void loginNtlm() throws Exception {
        System.setProperty("jdk.http.auth.tunneling.disabledSchemes", "");
        HttpURLConnection conn = openConnection(OA_BASE + "/gsdt/_api/web?$select=Title", "GET");
        String ntlmUser = USERNAME.contains("\\") ? USERNAME.split("\\\\")[1] : USERNAME;
        String auth = Base64.getEncoder().encodeToString((ntlmUser + ":" + PASSWORD).getBytes());
        conn.setRequestProperty("Authorization", "NTLM " + auth);
        conn.disconnect();
    }

    // ─── HTTP 工具 ───────────────────
    static HttpURLConnection openConnection(String url, String method) throws Exception {
        URI uri = new URI(url);
        HttpURLConnection conn = (HttpURLConnection) uri.toURL().openConnection();
        conn.setRequestMethod(method);
        conn.setInstanceFollowRedirects(false);
        conn.setConnectTimeout(REQUEST_TIMEOUT);
        conn.setReadTimeout(REQUEST_TIMEOUT);
        conn.setRequestProperty("User-Agent", "Mozilla/5.0 OA-Proxy/2.0");
        conn.setRequestProperty("Accept", "application/json;odata=verbose");
        List<HttpCookie> cookies = cookieManager.getCookieStore().getCookies();
        if (!cookies.isEmpty()) {
            StringBuilder sb = new StringBuilder();
            for (HttpCookie c : cookies) { if (sb.length()>0) sb.append("; "); sb.append(c.getName()).append("=").append(c.getValue()); }
            conn.setRequestProperty("Cookie", sb.toString());
        }
        return conn;
    }

    static String httpGet(String url) throws Exception {
        HttpURLConnection conn = openConnection(url, "GET");
        int code = conn.getResponseCode();
        String body = readStream(code >= 400 ? conn.getErrorStream() : conn.getInputStream());
        conn.disconnect();
        return body;
    }

    static String readStream(InputStream is) throws IOException {
        if (is == null) return "";
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        byte[] buf = new byte[8192]; int n;
        while ((n = is.read(buf)) != -1) bos.write(buf, 0, n);
        return bos.toString("UTF-8");
    }

    /** 从 HTTP 响应中提取 Set-Cookie 并存入 cookieManager */
    static void storeCookies(HttpURLConnection conn) {
        for (Map.Entry<String, List<String>> entry : conn.getHeaderFields().entrySet()) {
            if (entry.getKey() != null && entry.getKey().equalsIgnoreCase("Set-Cookie")) {
                for (String cookieHeader : entry.getValue()) {
                    String nameValue = cookieHeader.split(";")[0].trim();
                    int eq = nameValue.indexOf('=');
                    if (eq > 0) {
                        try {
                            URI uri = new URI(OA_BASE);
                            cookieManager.getCookieStore().add(uri,
                                new HttpCookie(nameValue.substring(0, eq).trim(),
                                              nameValue.substring(eq + 1).trim()));
                        } catch (Exception e) { /* ignore */ }
                    }
                }
            }
        }
    }

    /** 从 HTML 中提取 <input type="hidden" name="xxx" value="yyy"> 的 value */
    static String extractHtmlHidden(String html, String name) {
        int nameIdx = html.indexOf("name=\"" + name + "\"");
        if (nameIdx < 0) return "";
        int tagStart = html.lastIndexOf("<input", nameIdx);
        int tagEnd = html.indexOf(">", nameIdx);
        if (tagStart < 0 || tagEnd < 0) return "";
        String tag = html.substring(tagStart, tagEnd + 1);
        int valIdx = tag.indexOf("value=\"");
        if (valIdx >= 0) {
            valIdx += 7;
            int valEnd = tag.indexOf("\"", valIdx);
            return valEnd > valIdx ? tag.substring(valIdx, valEnd) : "";
        }
        return "";
    }

    static boolean isCookieExpired() {
        Date login = lastLogin.get();
        return login == null || (System.currentTimeMillis() - login.getTime()) > COOKIE_MAX_AGE_MS;
    }

    static String extractTitle(String json) {
        int i = json.indexOf("\"Title\":\"");
        if (i < 0) return "OK";
        i += 9; int j = json.indexOf("\"", i);
        return j > i ? json.substring(i, j) : "OK";
    }

    // ─── 门户主动拉取端点 ─────────────
    static class NewsApiHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            if (!"POST".equals(exchange.getRequestMethod())) {
                sendJson(exchange, 405, "{\"code\":-1,\"msg\":\"仅支持POST请求\"}");
                return;
            }

            try {
                // 1. 解析门户请求参数
                String body = readStream(exchange.getRequestBody());
                Map<String, String> params = parseForm(body);
                String typeId = params.getOrDefault("typeId", "gsdt");
                int maxCount = Math.min(Math.max(Integer.parseInt(params.getOrDefault("maxCount", "20")), 1), 100);
                int currentPage = Integer.parseInt(params.getOrDefault("currentPage", "1"));

                // 2. 映射typeId到SP路径
                String spPath = TYPE_PATH_MAP.get(typeId);
                if (spPath == null) {
                    sendJson(exchange, 400, "{\"code\":-1,\"msg\":\"未知分类: " + escapeJson(typeId) + "\"}");
                    return;
                }
                String typeName = TYPE_NAME_MAP.getOrDefault(typeId, typeId);

                logInfo("[拉取] typeId=" + typeId + " page=" + currentPage + " size=" + maxCount);

                String portalJson;
                if (testMode) {
                    // 测试模式：返回模拟数据
                    portalJson = buildMockData(typeId, typeName, currentPage, maxCount);
                    logInfo("[测试模式] 返回模拟数据 typeId=" + typeId);
                } else {
                    // 3. 确保登录
                    if (isCookieExpired()) { synchronized (OaProxyServer.class) { if (isCookieExpired()) loginSharePoint(); } }

                    // 4. 调用SP API（分页：$top + $skip）
                    int skip = (currentPage - 1) * maxCount;
                    String spUrl = OA_BASE + spPath + "_api/lists/getbytitle('%E9%A1%B5%E9%9D%A2')/items"
                        + "?$select=Created,Title,Id,ArticleStartDate,FileRef,Modified,PublishingPageContent"
                        + "&$top=" + maxCount
                        + "&$skip=" + skip
                        + "&$orderby=ArticleStartDate%20desc"
                        + "&$filter=OData__ModerationStatus%20eq%200";

                    String spResp = httpGet(spUrl);

                    // 5. 转换SP OData JSON → 门户消息列表JSON
                    portalJson = convertToPortalFormat(spResp, typeId, typeName, currentPage, maxCount);
                }

                // 6. 返回
                byte[] respBytes = portalJson.getBytes(StandardCharsets.UTF_8);
                exchange.getResponseHeaders().set("Content-Type", "application/json; charset=utf-8");
                exchange.sendResponseHeaders(200, respBytes.length);
                try (OutputStream os = exchange.getResponseBody()) { os.write(respBytes); }

            } catch (Exception e) {
                logSevere("[拉取错误] " + e);
                sendJson(exchange, 500, "{\"code\":-1,\"msg\":\"服务内部错误\"}");
            }
        }

        Map<String, String> parseForm(String body) {
            Map<String, String> map = new HashMap<>();
            if (body == null || body.isEmpty()) return map;
            for (String pair : body.split("&")) {
                String[] kv = pair.split("=", 2);
                if (kv.length == 2) {
                    try { map.put(kv[0], URLDecoder.decode(kv[1], "UTF-8")); }
                    catch (Exception e) { map.put(kv[0], kv[1]); }
                }
            }
            return map;
        }

        /**
         * SharePoint OData JSON → 门户消息列表JSON
         *
         * SP输入格式: {"d":{"results":[{"Title":"...","ArticleStartDate":"/Date(1751827200000)/","FileRef":"/gsdt/Pages/xxx.aspx"}]}}
         * 门户输出格式: {"code":0,"data":{"value":[{"name":"公司动态","value":[{"title":"...","createTime":"2026-07-06 14:40:00","jumpUrl":"http://..."}]}]}}
         */
        String convertToPortalFormat(String spJson, String typeId, String typeName, int page, int pageSize) {
            StringBuilder sb = new StringBuilder();
            sb.append("{\"code\":0,\"msg\":\"执行成功\",\"data\":{\"value\":[");
            sb.append("{\"name\":\"").append(escapeJson(typeName)).append("\"");
            sb.append(",\"typeId\":\"").append(escapeJson(typeId)).append("\"");
            sb.append(",\"currPage\":").append(page);
            sb.append(",\"pageSize\":").append(pageSize);

            // 提取SP results数组
            int resultsStart = spJson.indexOf("\"results\":[");
            if (resultsStart < 0) {
                sb.append(",\"totalCount\":0,\"totalPage\":0,\"value\":[]}]}}");
                return sb.toString();
            }
            int bracketEnd = findMatchingBracket(spJson, resultsStart + 10);

            // 统计条目
            String resultsArr = spJson.substring(resultsStart + 10, bracketEnd);
            int totalCount = countItems(resultsArr);
            int totalPage = (int) Math.ceil((double) totalCount / pageSize);

            sb.append(",\"totalCount\":").append(totalCount);
            sb.append(",\"totalPage\":").append(totalPage);
            sb.append(",\"value\":[");

            // 逐条转换
            List<String> items = splitJsonArray(resultsArr);
            for (int i = 0; i < items.size() && i < pageSize; i++) {
                if (i > 0) sb.append(",");
                sb.append(convertOneItem(items.get(i)));
            }

            sb.append("]}]");
            // moreUrl
            String spSitePath = TYPE_PATH_MAP.getOrDefault(typeId, "/gsdt/");
            sb.append(",\"moreUrl\":\"").append(OA_BASE).append(spSitePath).append("Pages/default.aspx\"");
            sb.append("}}");
            return sb.toString();
        }

        String convertOneItem(String spItem) {
            String title = extractJsonStringValue(spItem, "Title");
            String fileRef = extractJsonStringValue(spItem, "FileRef");
            String dateStr = extractJsonStringValue(spItem, "ArticleStartDate");
            if (dateStr.isEmpty()) dateStr = extractJsonStringValue(spItem, "Created");

            // PublishingPageContent 可能含转义 HTML，用安全提取方法
            String content = extractJsonStringValue(spItem, "PublishingPageContent");

            // 日期格式转换（支持 ISO 2026-07-21T01:41:35Z 和 MS /Date(1751827200000)/）
            String createTime = convertDate(dateStr);

            // FileRef: /gsdt/Pages/xxx.aspx → http://home.oa.gyzq.com/gsdt/Pages/xxx.aspx
            String jumpUrl = fileRef.isEmpty() ? "" : OA_BASE + fileRef;

            StringBuilder sb = new StringBuilder();
            sb.append("{\"title\":\"").append(escapeJson(title)).append("\"");
            sb.append(",\"content\":\"").append(escapeJson(content)).append("\"");
            sb.append(",\"image\":\"\"");
            sb.append(",\"subTitle\":\"国元证券\"");
            sb.append(",\"createTime\":\"").append(createTime).append("\"");
            sb.append(",\"appName\":\"老OA\"");
            sb.append(",\"jumpUrl\":\"").append(escapeJson(jumpUrl)).append("\"");
            sb.append(",\"publishUser\":\"\"}");
            return sb.toString();
        }

        /**
         * 提取 JSON 字符串值，正确处理转义字符（用于含 HTML 内容的字段）。
         * 支持转义引号、反斜杠、换行、unicode 等转义，也处理 null 值。
         */
        String extractJsonStringValue(String json, String fieldName) {
            String needle = "\"" + fieldName + "\"";
            int idx = json.indexOf(needle);
            if (idx < 0) return "";
            int colonIdx = json.indexOf(':', idx + needle.length());
            if (colonIdx < 0) return "";
            // 跳过空白
            int i = colonIdx + 1;
            while (i < json.length() && json.charAt(i) == ' ') i++;
            if (i >= json.length()) return "";
            // 处理 null
            if (json.charAt(i) == 'n' && json.startsWith("null", i)) return "";
            // 处理字符串值
            if (json.charAt(i) != '"') return "";
            i++; // 跳过开头的 "
            StringBuilder sb = new StringBuilder();
            while (i < json.length()) {
                char c = json.charAt(i);
                if (c == '\\' && i + 1 < json.length()) {
                    char next = json.charAt(i + 1);
                    switch (next) {
                        case '"':  sb.append('"');  i += 2; break;
                        case '\\': sb.append('\\'); i += 2; break;
                        case 'n':  sb.append('\n'); i += 2; break;
                        case 'r':  sb.append('\r'); i += 2; break;
                        case 't':  sb.append('\t'); i += 2; break;
                        case '/':  sb.append('/');  i += 2; break;
                        case 'u':
                            if (i + 5 < json.length()) {
                                try { sb.append((char) Integer.parseInt(json.substring(i+2, i+6), 16)); }
                                catch (NumberFormatException e) { sb.append("\\u").append(json.substring(i+2, i+6)); }
                                i += 6;
                            } else { i += 2; }
                            break;
                        default: sb.append('\\').append(next); i += 2; break;
                    }
                } else if (c == '"') {
                    return sb.toString();
                } else {
                    sb.append(c);
                    i++;
                }
            }
            return sb.toString();
        }

        /** 日期格式转换：支持 ISO (2026-07-21T01:41:35Z) 和 MS (/Date(1751827200000)/) */
        String convertDate(String dateStr) {
            if (dateStr == null || dateStr.isEmpty()) return "";
            // ISO 格式: 2026-07-21T01:41:35Z
            if (dateStr.contains("T") && dateStr.contains("-")) {
                try {
                    return dateStr.replace("T", " ").replace("Z", "");
                } catch (Exception e) { return dateStr; }
            }
            // MS Date 格式: /Date(1751827200000)/
            return convertMsDate(dateStr);
        }

        String convertMsDate(String msDate) {
            if (msDate.isEmpty()) return "";
            try {
                String num = msDate.replaceAll("[^0-9]", "");
                if (num.isEmpty()) return "";
                long ms = Long.parseLong(num);
                if (num.length() <= 10) ms *= 1000; // 秒转毫秒
                SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
                sdf.setTimeZone(TimeZone.getTimeZone("Asia/Shanghai"));
                return sdf.format(new Date(ms));
            } catch (Exception e) { return ""; }
        }

        int findMatchingBracket(String s, int start) {
            int depth = 1;
            for (int i = start + 1; i < s.length(); i++) {
                if (s.charAt(i) == '[') depth++;
                else if (s.charAt(i) == ']') { depth--; if (depth == 0) return i; }
            }
            return s.length() - 1;
        }

        int countItems(String arr) {
            int count = 0;
            int depth = 0;
            for (int i = 0; i < arr.length(); i++) {
                char c = arr.charAt(i);
                if (c == '{') depth++;
                else if (c == '}') { depth--; if (depth == 0) count++; }
            }
            return count;
        }

        List<String> splitJsonArray(String arr) {
            List<String> items = new ArrayList<>();
            int depth = 0, start = -1;
            for (int i = 0; i < arr.length(); i++) {
                char c = arr.charAt(i);
                if (c == '{') { if (depth == 0) start = i; depth++; }
                else if (c == '}') {
                    depth--;
                    if (depth == 0 && start >= 0) { items.add(arr.substring(start, i + 1)); start = -1; }
                }
            }
            return items;
        }

        // ─── 测试模式模拟数据 ─────────────
        String buildMockData(String typeId, String typeName, int page, int pageSize) {
            String[][] mockTitles = MOCK_NEWS_TITLES.getOrDefault(typeId, MOCK_NEWS_TITLES.get("gsdt"));
            int totalCount = mockTitles.length;
            int totalPage = (int) Math.ceil((double) totalCount / pageSize);
            String spSitePath = TYPE_PATH_MAP.getOrDefault(typeId, "/gsdt/");

            StringBuilder sb = new StringBuilder();
            sb.append("{\"code\":0,\"msg\":\"执行成功\",\"data\":{\"value\":[");
            sb.append("{\"name\":\"").append(escapeJson(typeName)).append("\"");
            sb.append(",\"typeId\":\"").append(escapeJson(typeId)).append("\"");
            sb.append(",\"currPage\":").append(page);
            sb.append(",\"pageSize\":").append(pageSize);
            sb.append(",\"totalCount\":").append(totalCount);
            sb.append(",\"totalPage\":").append(totalPage);
            sb.append(",\"value\":[");

            int start = (page - 1) * pageSize;
            int end = Math.min(start + pageSize, totalCount);
            for (int i = start; i < end; i++) {
                if (i > start) sb.append(",");
                sb.append("{\"title\":\"").append(escapeJson(mockTitles[i][0])).append("\"");
                sb.append(",\"content\":\"<p>这是模拟的新闻正文内容，仅用于测试模式。</p>\"");
                sb.append(",\"image\":\"\"");
                sb.append(",\"subTitle\":\"国元证券\"");
                sb.append(",\"createTime\":\"").append(mockTitles[i][1]).append("\"");
                sb.append(",\"appName\":\"老OA\"");
                sb.append(",\"jumpUrl\":\"").append(OA_BASE).append(spSitePath).append("Pages/test").append(i + 1).append(".aspx\"");
                sb.append(",\"publishUser\":\"\"}");
            }

            sb.append("]}]");
            sb.append(",\"moreUrl\":\"").append(OA_BASE).append(spSitePath).append("Pages/default.aspx\"");
            sb.append("}}");
            return sb.toString();
        }

        // 每个typeId的模拟新闻：[标题, 日期]
        static final Map<String, String[][]> MOCK_NEWS_TITLES = new LinkedHashMap<>();
        static {
            MOCK_NEWS_TITLES.put("gsdt", new String[][]{
                {"【公司动态】2026年半年度经营分析会顺利召开", "2026-07-20 09:30:00"},
                {"【公司动态】国元证券荣获\u201c最佳投行\u201d称号", "2026-07-18 14:00:00"},
                {"【公司动态】公司党委召开主题教育总结大会", "2026-07-15 10:00:00"}
            });
            MOCK_NEWS_TITLES.put("bmjb", new String[][]{
                {"【部门简报】投行部完成三单IPO项目过会", "2026-07-19 16:00:00"},
                {"【部门简报】财富管理部推出新版客户服务体系", "2026-07-17 11:00:00"},
                {"【部门简报】研究所发布2026年中期策略报告", "2026-07-14 09:00:00"}
            });
            MOCK_NEWS_TITLES.put("cxfz", new String[][]{
                {"【创新发展】公司智能投顾平台正式上线运行", "2026-07-21 08:30:00"},
                {"【创新发展】数字化转型二期项目启动会召开", "2026-07-16 15:00:00"},
                {"【创新发展】金融科技实验室与高校签署合作协议", "2026-07-12 10:30:00"}
            });
            MOCK_NEWS_TITLES.put("jgdt", new String[][]{
                {"【监管动态】证监会发布证券公司分类评价新规", "2026-07-20 17:00:00"},
                {"【监管动态】安徽证监局开展辖区合规检查工作", "2026-07-17 14:30:00"},
                {"【监管动态】证券业协会修订从业人员管理办法", "2026-07-13 09:00:00"}
            });
            MOCK_NEWS_TITLES.put("djqt", new String[][]{
                {"【党建群团】公司团委举办青年员工座谈会", "2026-07-19 10:00:00"},
                {"【党建群团】机关党支部开展主题党日活动", "2026-07-16 16:30:00"},
                {"【党建群团】工会组织夏季送清凉慰问活动", "2026-07-11 11:00:00"}
            });
            MOCK_NEWS_TITLES.put("zgs", new String[][]{
                {"【子公司】国元股权投资完成新一轮基金募集", "2026-07-18 15:30:00"},
                {"【子公司】国元期货获批商品期权做市商资格", "2026-07-15 10:00:00"},
                {"【子公司】国元创新投资参与科创板战略配售", "2026-07-10 14:00:00"}
            });
            MOCK_NEWS_TITLES.put("lxyz", new String[][]{
                {"【党建指南】关于开展2026年度民主评议党员的通知", "2026-07-20 08:00:00"},
                {"【党建指南】基层党组织换届选举工作指引", "2026-07-17 09:30:00"},
                {"【党建指南】\u201c学习强国\u201d学习平台积分管理办法", "2026-07-13 16:00:00"}
            });
        }

        String escapeJson(String s) {
            if (s == null) return "";
            return s.replace("\\", "\\\\")
                    .replace("\"", "\\\"")
                    .replace("\n", "\\n")
                    .replace("\r", "")
                    .replace("\t", " ");
        }

        void sendJson(HttpExchange exchange, int code, String json) throws IOException {
            byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().set("Content-Type", "application/json; charset=utf-8");
            exchange.sendResponseHeaders(code, bytes.length);
            try (OutputStream os = exchange.getResponseBody()) { os.write(bytes); }
        }
    }

    // ─── 健康检查 ─────────────────
    static class HealthHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            long uptime = (System.currentTimeMillis() - START_TIME) / 1000;
            String json = "{\"status\":\"UP\",\"uptime_seconds\":" + uptime + ",\"oa_base\":\"" + OA_BASE + "\"}";
            byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().set("Content-Type", "application/json; charset=utf-8");
            exchange.sendResponseHeaders(200, bytes.length);
            try (OutputStream os = exchange.getResponseBody()) { os.write(bytes); }
        }
    }
}
