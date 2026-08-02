#!/usr/bin/env python3
"""
OA新闻代理服务 — 部署到客户生产服务器
用途：代理智能门户前端请求到老OA SharePoint，自动管理Cookie认证

部署路径：/opt/oa-news-proxy/
服务管理：systemctl start|stop|restart oa-proxy
"""

import json
import logging
import os
import signal
import sys
import time
import threading
import urllib.parse
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ─── 配置加载 ───────────────────────────────────────────────
CONFIG_FILE = Path(__file__).parent / "oa_config.json"


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


cfg = load_config()

# ─── 日志 ───────────────────────────────────────────────────
LOG_FILE = cfg.get("logging", {}).get("file", "/var/log/oa-proxy/proxy.log")
LOG_LEVEL = getattr(logging, cfg.get("logging", {}).get("level", "INFO"))
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("oa-proxy")

# ─── 全局状态 ───────────────────────────────────────────────
OA_BASE = cfg["oa"]["base_url"].rstrip("/")
LISTEN = (cfg["proxy"]["listen_host"], cfg["proxy"]["listen_port"])
SESSION = requests.Session()
SESSION_LOCK = threading.Lock()
COOKIE_EXPIRY = timedelta(hours=cfg["session"]["cookie_max_age_hours"])
_last_login = None
_retry_config = Retry(
    total=cfg["session"]["retry_count"],
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504],
)
SESSION.mount("http://", HTTPAdapter(max_retries=_retry_config))
SESSION.mount("https://", HTTPAdapter(max_retries=_retry_config))
TIMEOUT = cfg["session"]["request_timeout"]

# 需要代理的新闻分类路径映射（OA子站路径 → 门户代理路径前缀）
# 这个映射被反向使用：门户请求 /oa-news/gsdt/xxx → OA /gsdt/xxx
PATH_MAP = {
    "/oa-news/gsdt/":     "/gsdt/",           # 公司动态
    "/oa-news/bmjb/":     "/bmjb/",           # 部门简报
    "/oa-news/cxfz/":     "/cxfz/",           # 创新发展
    "/oa-news/hggl/":     "/hggl/",           # 合规管理-监管动态
    "/oa-news/djqt/":     "/gsdt/djqt/",      # 党建群团
    "/oa-news/zgs/":      "/gsdt/zgsfzjg/",   # 子公司及分支机构
    "/oa-news/lxyz/":     "/jdlm/lxyz/",      # 党建指南
    "/oa-news/fwt/":      "/jdlm/fwt/",       # 服务台
    "/oa-news/bmgg/":     "/",                # 部门公告（Search API，根路径）
}


# ─── SharePoint 认证 ─────────────────────────────────────────

def login_sharepoint():
    """登录SharePoint获取认证Cookie，返回cookies字典"""
    global _last_login

    auth_type = cfg["oa"]["auth_type"]
    username = cfg["credentials"]["username"]
    password = cfg["credentials"]["password"]

    log.info("登录OA: %s (认证方式: %s)", OA_BASE, auth_type)
    session = requests.Session()

    try:
        if auth_type == "cookie_form":
            cookies = _login_via_form(session, username, password)
        elif auth_type == "ntlm":
            from requests_ntlm import HttpNtlmAuth
            session.auth = HttpNtlmAuth(username, password)
            cookies = _login_via_ntlm(session)
        else:
            raise ValueError(f"不支持的认证类型: {auth_type}")

        _last_login = datetime.now()
        log.info("OA登录成功，获取到 %d 个Cookie", len(cookies))
        return cookies

    except Exception as e:
        log.error("OA登录失败: %s", e)
        raise


def _login_via_form(session, username, password):
    """表单认证登录（SharePoint FBA）"""
    # Step 1: 获取登录页面，提取必要的隐藏字段
    login_url = OA_BASE + cfg["oa"]["login_page"]
    resp = session.get(login_url, timeout=TIMEOUT)
    resp.raise_for_status()

    # Step 2: 构造登录请求
    # SharePoint FBA 通常POST到 /_forms/default.aspx 或 /_layouts/15/Authenticate.aspx
    # 具体字段取决于SharePoint版本和配置
    login_data = {
        "ctl00$PlaceHolderMain$SignInControl$UserName": username,
        "ctl00$PlaceHolderMain$SignInControl$password": password,
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
    }

    resp = session.post(login_url, data=login_data, timeout=TIMEOUT, allow_redirects=True)

    # Step 3: 验证是否登录成功（检查返回页面是否包含登录表单）
    if "SignInControl" in resp.text or "login" in resp.text.lower():
        # 尝试备用登录方式：/signin
        alt_login_url = f"{OA_BASE}/signin"
        resp = session.get(alt_login_url, timeout=TIMEOUT)
        alt_data = {
            "login": username,
            "passwd": password,
            "LoginOptions": "1",
        }
        resp = session.post(alt_login_url, data=alt_data, timeout=TIMEOUT, allow_redirects=True)

    # Step 4: 验证API是否能正常访问
    test_url = f"{OA_BASE}/gsdt/_api/web/title"
    resp = session.get(test_url, timeout=TIMEOUT)
    if resp.status_code == 401:
        raise RuntimeError(
            f"登录失败(401): 用户名密码可能错误，或SharePoint配置了其他认证方式。"
            f"请检查 {CONFIG_FILE} 中的 username/password/auth_type"
        )
    if resp.status_code != 200:
        raise RuntimeError(f"登录验证失败(HTTP {resp.status_code}): {resp.text[:200]}")

    log.info("登录验证通过: %s", resp.json().get("d", {}).get("Title", "OK"))
    return session.cookies.get_dict()


def _login_via_ntlm(session):
    """NTLM认证登录"""
    test_url = f"{OA_BASE}/gsdt/_api/web/title"
    resp = session.get(test_url, timeout=TIMEOUT)
    if resp.status_code == 401:
        raise RuntimeError("NTLM认证失败(401): 用户名密码错误")
    resp.raise_for_status()
    log.info("NTLM登录验证通过: %s", resp.json().get("d", {}).get("Title", "OK"))
    return session.cookies.get_dict()


def ensure_logged_in():
    """确保Session有效，过期则重新登录"""
    with SESSION_LOCK:
        if _last_login is None or (datetime.now() - _last_login) > COOKIE_EXPIRY:
            cookies = login_sharepoint()
            SESSION.cookies.clear()
            SESSION.cookies.update(cookies)


# ─── HTTP 代理服务 ──────────────────────────────────────────

class OAProxyHandler(BaseHTTPRequestHandler):
    """将门户请求代理到OA SharePoint，自动注入Cookie"""

    def do_GET(self):
        self._proxy_request("GET")

    def do_POST(self):
        self._proxy_request("POST")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _proxy_request(self, method):
        try:
            # 1. 路由映射：/oa-news/gsdt/_api/... → OA /gsdt/_api/...
            target_path = self._map_path(self.path)
            if target_path is None:
                self.send_error(404, f"Unknown proxy path: {self.path}")
                return

            # 2. 拼接完整OA URL
            parsed = urllib.parse.urlparse(self.path)
            oa_url = OA_BASE + target_path
            if parsed.query:
                oa_url += "?" + parsed.query

            log.info("[%s] %s → %s", method, self.path, oa_url)

            # 3. 确保已登录
            ensure_logged_in()

            # 4. 转发请求
            headers = {k: v for k, v in self.headers.items()
                       if k.lower() not in ("host", "cookie")}
            headers["Host"] = "home.oa.gyzq.com"

            with SESSION_LOCK:
                resp = SESSION.request(
                    method=method,
                    url=oa_url,
                    headers=headers,
                    timeout=TIMEOUT,
                    allow_redirects=False,
                )

            # 5. 返回响应
            self.send_response(resp.status_code)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Type",
                             resp.headers.get("Content-Type", "application/json; charset=utf-8"))

            # 透传关键响应头
            for h in ("Cache-Control", "Expires", "ETag", "Last-Modified"):
                if h in resp.headers:
                    self.send_header(h, resp.headers[h])

            self.end_headers()

            # 流式写入响应体（支持大响应，如Search API的100条记录）
            if resp.encoding is None:
                resp.encoding = "utf-8"
            self.wfile.write(resp.content)

        except requests.exceptions.Timeout:
            log.error("[TIMEOUT] %s → %s", self.path, oa_url)
            self.send_error(504, "OA upstream timeout")
        except requests.exceptions.ConnectionError as e:
            log.error("[CONNECT] %s → %s: %s", self.path, oa_url, e)
            self.send_error(502, f"Cannot connect to OA: {e}")
        except Exception as e:
            log.error("[ERROR] %s: %s", self.path, e, exc_info=True)
            self.send_error(500, str(e))

    def _map_path(self, path):
        """将门户请求路径映射到OA实际路径"""
        for portal_prefix, oa_prefix in PATH_MAP.items():
            if path.startswith(portal_prefix):
                # /oa-news/gsdt/_api/xxx → /gsdt/_api/xxx
                rest = path[len(portal_prefix):]
                return oa_prefix.lstrip("/") + "/" + rest.lstrip("/")

        # 如果没有匹配，检查是否是合法路径
        log.warning("未匹配的路径: %s", path)
        return None

    def log_message(self, format, *args):
        log.info("[HTTP] %s", format % args)


# ─── 主程序 ─────────────────────────────────────────────────

def run_server():
    server = HTTPServer(LISTEN, OAProxyHandler)
    log.info("=" * 60)
    log.info("OA新闻代理服务启动")
    log.info("监听地址: %s:%d", LISTEN[0], LISTEN[1])
    log.info("OA目标:   %s", OA_BASE)
    log.info("日志文件: %s", LOG_FILE)
    log.info("Cookie有效期: %d小时", cfg["session"]["cookie_max_age_hours"])
    log.info("=" * 60)

    def shutdown(sig, frame):
        log.info("收到停止信号，正在关闭...")
        server.shutdown()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        log.info("OA新闻代理服务已停止")


if __name__ == "__main__":
    # 启动时先测试登录能否成功
    try:
        log.info("启动前验证OA登录...")
        ensure_logged_in()
        log.info("OA登录验证成功 ✅")
    except Exception as e:
        log.critical("OA登录失败，服务无法启动: %s", e)
        log.critical("请检查 %s 中的配置是否正确", CONFIG_FILE)
        sys.exit(1)

    run_server()
