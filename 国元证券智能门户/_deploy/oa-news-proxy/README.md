# OA新闻代理 — 生产部署包

**用途**：将老OA（SharePoint）新闻接口通过Nginx代理注入Cookie，同步新闻数据到智能门户。  
**编制**：王昭 | **日期**：2026-07-16 | **适用环境**：银河麒麟 V10 / CentOS 7+

---

## 文件结构

```
oa-news-proxy/
├── deploy.sh                      # 一键部署脚本（在接入机上执行）
├── README.md                      # 本文档
├── nginx/
│   └── oa-news-proxy.conf         # Nginx配置文件
└── scripts/
    ├── oa_proxy.py                # Python代理服务（核心）
    ├── oa_config.json             # 配置文件（需修改账号密码）
    ├── oa-proxy.service           # systemd服务文件
    └── verify.sh                  # 部署验证脚本
```

---

## 快速部署（3步）

### 第1步：配置OA账号

编辑 `scripts/oa_config.json`，填写OA服务账号：

```json
{
    "credentials": {
        "username": "OA服务账号",
        "password": "密码"
    }
}
```

> ⚠️ auth_type 默认为 `cookie_form`（表单认证）。如果OA使用Windows集成认证（NTLM），改为 `ntlm`。

### 第2步：执行部署脚本

将整个 `oa-news-proxy/` 文件夹传到门户应用服务器(10.0.63.11)，然后执行：

```bash
cd /path/to/oa-news-proxy
chmod +x deploy.sh
sudo bash deploy.sh
```

脚本会自动：
- 检查环境（nginx/python3/requests）
- 部署文件到 `/opt/oa-news-proxy/`
- 配置Nginx代理规则
- 注册systemd服务
- 提示启动服务

### 第3步：验证

```bash
bash /opt/oa-news-proxy/verify.sh portal.oa.gyzq.com
```

验证通过后，在门户后台配置新闻数据源URL。

---

## 数据源配置（门户侧）

验证通过后，在门户「门户装修 → 首页编辑 → 新闻组件」中配置HTTP数据源：

**示例：公司动态**
```
https://portal.oa.gyzq.com/oa-news/gsdt/_api/lists/getbytitle('页面')/items?$select=Created,Title,Id,ArticleStartDate,FileRef,Modified&$top=20&$orderby=ArticleStartDate%20desc&$filter=OData__ModerationStatus%20eq%200
```

各分类对应的路径前缀：

| 新闻分类 | 代理路径前缀 |
|---------|------------|
| 公司动态 | `/oa-news/gsdt/` |
| 部门简报 | `/oa-news/bmjb/` |
| 创新发展 | `/oa-news/cxfz/zcdt/` |
| 监管动态 | `/oa-news/hggl/jgdt/` |
| 党建群团 | `/oa-news/djqt/` |
| 子公司及分支机构 | `/oa-news/zgs/` |
| 党建指南 | `/oa-news/lxyz/` |
| 服务台 | `/oa-news/fwt/{子站名}/` |
| 部门公告 | `/oa-news/bmgg/` |

配置要求：
- 数据源类型：HTTP / REST API
- 请求方式：GET
- 认证方式：**无需认证**（Nginx已代为处理）
- 刷新频率：建议10分钟

---

## 服务管理

```bash
# 启动/停止/重启
systemctl start   oa-proxy
systemctl stop    oa-proxy
systemctl restart oa-proxy

# 查看状态
systemctl status  oa-proxy

# 查看日志
journalctl -u oa-proxy -f           # 实时日志
journalctl -u oa-proxy -n 100       # 最近100行

# 日志文件
tail -f /var/log/oa-proxy/proxy.log
```

---

## 工作原理

```
浏览器(门户) → GET /oa-news/gsdt/_api/...
    ↓
Nginx(接入机) → proxy_pass http://127.0.0.1:8899
    ↓
oa_proxy.py(本地) → 自动注入OA Cookie → GET http://home.oa.gyzq.com/gsdt/_api/...
    ↓
SharePoint返回JSON → 代理透传 → 门户组件渲染
```

- Python代理服务监听 `127.0.0.1:8899`（仅本机）
- 启动时自动登录OA获取Cookie
- Cookie过期后自动重新登录（默认4小时）
- 线程安全，支持并发请求

---

## 故障排查

| 现象 | 可能原因 | 解决方法 |
|------|---------|---------|
| 验证脚本报 401 | Cookie过期/账号密码错误 | 检查 oa_config.json，重启服务 |
| 验证脚本报 502 | Python代理未启动 | `systemctl status oa-proxy`，查看日志 |
| 验证脚本报 504 | OA响应超时 | 检查网络，调大 timeout |
| 验证脚本报 503 | 代理服务异常 | `journalctl -u oa-proxy -n 50` 查看错误 |
| Nginx配置失败 | conf.d未被include | 在nginx.conf中加 `include /etc/nginx/conf.d/*.conf;` |
| 登录失败 | auth_type错误 | 尝试把 `cookie_form` 改为 `ntlm` |

---

## 安全说明

- `oa_config.json` 包含OA账号密码，权限已设为 `600`（仅root可读）
- 代理服务仅监听 `127.0.0.1`，不对外暴露端口
- OA Cookie不会写入浏览器或日志文件
- 生产部署后建议定期更换OA密码

---

## 附：纯Nginx方案（无Python依赖）

如果生产环境不允许运行Python服务，可以使用纯Nginx方案，手动管理Cookie：

**适用场景**：Cookie有效期较长（如24小时），运维人员可定期手动更新。

**Nginx配置**（替换oa-news-proxy.conf）：

```nginx
location /oa-news/ {
    # 硬编码OA Cookie（手动从浏览器获取后粘贴到这里）
    # Cookie来源：浏览器F12 → Application → Cookies → home.oa.gyzq.com
    proxy_set_header Cookie "FedAuth=xxx; rtFa=xxx";
    
    proxy_pass http://home.oa.gyzq.com/;
    proxy_set_header Host home.oa.gyzq.com;
    proxy_connect_timeout 5s;
    proxy_read_timeout 15s;
}
```

**获取Cookie步骤**：
1. 用OA服务账号在浏览器登录 `http://home.oa.gyzq.com`
2. F12 → Application → Cookies → 选中 `home.oa.gyzq.com`
3. 复制 `FedAuth` 和 `rtFa` 的值
4. 粘贴到Nginx配置中
5. `nginx -t && nginx -s reload`

**缺点**：Cookie过期后需手动更新（通常每8-10小时一次）。
