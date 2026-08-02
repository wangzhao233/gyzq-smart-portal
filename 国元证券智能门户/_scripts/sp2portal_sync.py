#!/usr/bin/env python3
"""
国元证券 OA 新闻 → 智能门户 数据同步脚本
=========================================
流程：
  1. 从 Keycloak SSO 获取 access_token（或读取 Cookie）
  2. 调用 SharePoint REST API 拉取新闻列表
  3. 解析 Atom XML → 提取字段
  4. 转换为门户推送格式
  5. POST 到门户数据源推送接口
  6. 增量同步：记录已推送数据的时间戳

依赖：pip install requests pyyaml
"""

import json
import logging
import os
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
import yaml

# ── 日志 ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("sp2portal")

# ── 常量 ──────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.yaml")
STATE_PATH = os.path.join(SCRIPT_DIR, "sync_state.json")

# SharePoint Atom XML 命名空间
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "d": "http://schemas.microsoft.com/ado/2007/08/dataservices",
    "m": "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
}


# ═══════════════════════════════════════════════════════
#  1. 配置加载
# ═══════════════════════════════════════════════════════
def load_config(path: str = CONFIG_PATH) -> dict:
    """加载 YAML 配置"""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ═══════════════════════════════════════════════════════
#  2. 认证
# ═══════════════════════════════════════════════════════
def get_access_token(cfg: dict) -> str:
    """通过 Keycloak 直接授权获取 access_token"""
    kc = cfg["keycloak"]
    if not kc.get("enabled"):
        raise RuntimeError("Keycloak 认证未启用")

    log.info("正在通过 Keycloak 获取 access_token ...")
    resp = requests.post(
        kc["url"],
        data={
            "grant_type": "password",
            "client_id": kc["client_id"],
            "username": kc["username"],
            "password": kc["password"],
        },
        timeout=15,
    )

    if resp.status_code != 200:
        log.error(f"Keycloak 认证失败 [{resp.status_code}]: {resp.text}")
        raise RuntimeError(f"Keycloak 认证失败: {resp.status_code}")

    data = resp.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError("Keycloak 响应中未找到 access_token")

    log.info(f"✓ access_token 获取成功，有效期 {data.get('expires_in', '?')} 秒")
    return token


def load_cookie_session(cfg: dict) -> requests.Session:
    """从 Cookie 文件加载会话（Keycloak 不可用时的备选）"""
    session = requests.Session()
    cookie_file = cfg["cookie_auth"].get("cookie_file", "cookie.txt")
    path = os.path.join(SCRIPT_DIR, cookie_file)

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Cookie 文件 {path} 不存在。\n"
            "请在浏览器登录 OA 后，从开发者工具 → Application → Cookies 导出。"
        )

    import http.cookiejar

    cj = http.cookiejar.MozillaCookieJar(path)
    cj.load()
    session.cookies.update(cj)
    log.info(f"✓ 已从 {path} 加载 Cookie")
    return session


# ═══════════════════════════════════════════════════════
#  3. 拉取 SharePoint 新闻
# ═══════════════════════════════════════════════════════
def build_sp_url(cfg: dict) -> str:
    """构建 SharePoint REST API URL"""
    sp = cfg["sp"]
    # URL 编码列表名
    from urllib.parse import quote

    list_name = quote(sp["list_name"])
    q = sp["query"]
    params = (
        f"?$select={q['$select']}"
        f"&$top={q['$top']}"
        f"&$orderby={q['$orderby']}"
        f"&$filter={q['$filter']}"
    )
    return f"{sp['base_url']}{sp['site_path']}/_api/lists/getbytitle('{list_name}')/items{params}"


def fetch_news(
    token: str, session: Optional[requests.Session], cfg: dict
) -> List[Dict[str, Any]]:
    """调用 SharePoint API 获取新闻列表"""
    url = build_sp_url(cfg)
    headers = {
        "Accept": "application/json;odata=verbose",
        "Content-Type": "application/json;odata=verbose",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    kwargs = {"headers": headers, "timeout": 30}
    if session:
        kwargs["cookies"] = session.cookies

    log.info(f"正在拉取 SharePoint 新闻: {sp['query']['$top']} 条")
    log.debug(f"URL: {url}")

    resp = requests.get(url, **kwargs)

    if resp.status_code == 401:
        log.error("SharePoint API 返回 401，认证失败")
        log.error("  可能原因：Keycloak token 无效 / Cookie 过期 / 账号无权限")
        resp.raise_for_status()

    if resp.status_code != 200:
        log.error(f"API 请求失败 [{resp.status_code}]: {resp.text[:300]}")
        resp.raise_for_status()

    # 尝试 JSON 解析
    try:
        data = resp.json()
        log.info(f"✓ 返回 JSON 格式")
        return parse_json_response(data, cfg)
    except (json.JSONDecodeError, ValueError):
        # 回落 XML 解析
        log.info(f"✓ 返回 XML 格式，切换解析器")
        return parse_xml_response(resp.text, cfg)


# ═══════════════════════════════════════════════════════
#  4. 响应解析
# ═══════════════════════════════════════════════════════
def parse_json_response(data: dict, cfg: dict) -> List[Dict[str, Any]]:
    """解析 SharePoint JSON 响应（odata=verbose 格式）"""
    sp = cfg["sp"]
    detail_base = cfg["mapping"]["detail_base_url"]

    results = data.get("d", {}).get("results", [])
    if not results:
        log.warning("JSON 响应中未找到数据 (d.results)")
        return []

    items = []
    for item in results:
        items.append(_normalize_item(item, detail_base))

    log.info(f"解析到 {len(items)} 条新闻")
    return items


def parse_xml_response(xml_text: str, cfg: dict) -> List[Dict[str, Any]]:
    """解析 SharePoint Atom XML 响应"""
    sp = cfg["sp"]
    detail_base = cfg["mapping"]["detail_base_url"]

    root = ET.fromstring(xml_text)
    entries = root.findall("atom:entry", NS)

    if not entries:
        log.warning("XML 响应中未找到 entry 节点")
        return []

    items = []
    for entry in entries:
        props = entry.find(".//m:properties", NS)
        if props is None:
            continue

        raw = {}
        for child in props:
            tag = child.tag.split("}")[-1]  # 去掉 namespace
            raw[tag] = child.text or ""

        items.append(_normalize_item(raw, detail_base))

    log.info(f"解析到 {len(items)} 条新闻")
    return items


def _normalize_item(raw: dict, detail_base: str) -> Dict[str, Any]:
    """标准化单条新闻记录"""
    title = raw.get("Title") or raw.get("title") or ""
    item_id = raw.get("Id") or raw.get("ID") or raw.get("id") or ""
    file_ref = raw.get("FileRef") or raw.get("fileRef") or ""
    article_date = (
        raw.get("ArticleStartDate") or raw.get("articleStartDate") or ""
    )
    created = raw.get("Created") or raw.get("created") or ""

    # 处理 /Date(时间戳)/ 格式
    date_str = article_date or created

    # 拼接详情 URL
    jump_url = detail_base + file_ref if file_ref else ""

    return {
        "id": str(item_id) if item_id else "",
        "title": title,
        "date": date_str,
        "jump_url": jump_url,
        "file_ref": file_ref,
    }


# ═══════════════════════════════════════════════════════
#  5. 推送到门户
# ═══════════════════════════════════════════════════════
def push_to_portal(
    items: List[Dict[str, Any]], cfg: dict
) -> int:
    """将数据推送到门户数据源推送接口"""
    portal = cfg["portal"]
    url = (
        f"{portal['domain']}/data_sources"
        f"/{portal['tenant_id']}/{portal['data_source_id']}/push"
    )

    # 构建 jsonData（信息列表格式）
    json_data = []
    for item in items:
        json_data.append(
            {
                "title": item["title"],
                "infoId": item["id"],
                "jumpUrl": item["jump_url"],
                "subTitle": _format_date(item["date"]),
                "image": "",
                "dataType": cfg["mapping"]["data_type"],
                "users": "",
                "departments": "",
                "tags": "",
            }
        )

    payload = {
        "secret": portal["secret"],
        "jsonData": json_data,
        "dataSourceOperate": "SAVE_UPDATE",
    }

    log.info(f"正在推送 {len(json_data)} 条数据到门户...")
    log.debug(f"推送 URL: {url}")

    resp = requests.post(
        url,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )

    if resp.status_code not in (200, 201):
        log.error(
            f"推送失败 [{resp.status_code}]: {resp.text[:500]}"
        )
        resp.raise_for_status()

    result = resp.json()
    log.info(f"✓ 推送成功: {result}")
    return len(json_data)


def _format_date(date_str: str) -> str:
    """格式化日期：ISO字符串 → YYYY-MM-DD HH:mm"""
    if not date_str:
        return ""

    # 处理 /Date(1712345678000)/ 格式
    if date_str.startswith("/Date("):
        try:
            ts = int(date_str[6:-2]) / 1000  # 毫秒→秒
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, IndexError):
            return date_str

    # 处理 ISO 格式 2026-07-07T06:45:06Z
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return date_str[:16] if date_str else ""


# ═══════════════════════════════════════════════════════
#  6. 增量同步
# ═══════════════════════════════════════════════════════
def load_state() -> dict:
    """加载上次同步状态"""
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_sync": "", "pushed_ids": []}


def save_state(state: dict):
    """保存同步状态"""
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def filter_new_items(
    items: List[Dict[str, Any]], state: dict
) -> List[Dict[str, Any]]:
    """过滤已推送过的数据"""
    pushed_ids = set(state.get("pushed_ids", []))
    new_items = [i for i in items if i["id"] not in pushed_ids]

    if len(new_items) < len(items):
        log.info(
            f"过滤掉 {len(items) - len(new_items)} 条已推送数据，"
            f"新增 {len(new_items)} 条"
        )
    return new_items


def update_state(items: List[Dict[str, Any]], state: dict):
    """更新同步状态"""
    now = datetime.now(timezone.utc).isoformat()
    pushed_ids = set(state.get("pushed_ids", []))
    new_ids = {i["id"] for i in items if i["id"]}
    pushed_ids.update(new_ids)

    # 只保留最近 500 条 ID（避免状态文件膨胀）
    pushed_list = sorted(pushed_ids, reverse=True)[:500]

    state.update(
        {
            "last_sync": now,
            "pushed_ids": pushed_list,
        }
    )
    save_state(state)
    log.info(f"状态已更新，共记录 {len(pushed_list)} 条已推送 ID")


# ═══════════════════════════════════════════════════════
#  7. 主流程
# ═══════════════════════════════════════════════════════
def main():
    log.info("=" * 50)
    log.info("国元证券 OA 新闻 → 智能门户 同步开始")
    log.info("=" * 50)

    # 加载配置
    cfg = load_config()

    # 验证关键配置
    portal = cfg["portal"]
    missing = []
    if "REPLACE_WITH" in portal.get("tenant_id", ""):
        missing.append("tenant_id")
    if "REPLACE_WITH" in portal.get("data_source_id", ""):
        missing.append("data_source_id")
    if "REPLACE_WITH" in portal.get("secret", ""):
        missing.append("secret")

    if missing:
        log.error(
            f"配置不完整，以下项需要从门户后台获取并填写到 config.yaml：\n"
            f"  - portal.{', portal.'.join(missing)}\n\n"
            f"获取路径：门户管理后台 → 数据&集成 → 数据源 → 新建/查看数据源"
        )
        sys.exit(1)

    # Step 1: 获取 access_token
    try:
        token = get_access_token(cfg)
        session = None
    except Exception as e:
        log.warning(f"Keycloak 认证失败 ({e})，尝试 Cookie 方式...")
        if cfg["cookie_auth"].get("enabled"):
            try:
                session = load_cookie_session(cfg)
                token = ""
            except Exception as ce:
                log.error(f"Cookie 加载也失败了: {ce}")
                sys.exit(1)
        else:
            log.error("Keycloak 认证失败且未启用 Cookie 认证。")
            log.error("请检查：1) 账号密码 2) Keycloak 服务可达 3) 启用 cookie_auth")
            sys.exit(1)

    # Step 2: 拉取新闻
    try:
        all_items = fetch_news(token, session, cfg)
    except Exception as e:
        log.error(f"拉取新闻失败: {e}")
        sys.exit(1)

    if not all_items:
        log.warning("没有获取到新闻数据，结束同步")
        return

    # Step 3: 增量过滤
    state = load_state()
    new_items = filter_new_items(all_items, state)

    if not new_items:
        log.info("没有新增新闻，跳过推送")
        # 只更新时间戳
        state["last_sync"] = datetime.now(timezone.utc).isoformat()
        save_state(state)
        return

    # Step 4: 推送到门户
    try:
        pushed = push_to_portal(new_items, cfg)
    except Exception as e:
        log.error(f"推送到门户失败: {e}")
        sys.exit(1)

    # Step 5: 更新状态
    update_state(new_items, state)

    log.info(f"✓ 同步完成: 拉取 {len(all_items)} 条, 新增推送 {pushed} 条")


if __name__ == "__main__":
    main()
