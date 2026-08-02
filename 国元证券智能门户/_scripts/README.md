# OA新闻同步脚本 — 使用说明

## 文件结构

```
_scripts/
├── config.yaml          # 🔧 配置（需要你填）
├── sp2portal_sync.py    # 🚀 主同步脚本
├── sync_state.json       # 📝 自动生成：同步状态
└── cookie.txt            # 🍪 备用：从浏览器导出的 Cookie
```

## 使用前准备

### 1. 安装依赖

```bash
cd C:\Users\11039\WorkBuddy\国元证券智能门户\_scripts
python -m pip install requests pyyaml
```

### 2. 获取门户推送信息

门户管理后台 → 数据&集成 → 数据源 → **新建数据源**（类型选信息列表）

创建完后你会得到：
- **推送URL**: `https://portal.oa.gyzq.com/data_sources/{tenantId}/{dataSourceId}/push`
- **Secret**: 一串密钥

把上述值填入 `config.yaml` 的 `portal` 段。

### 3. 测试 Keycloak 认证

在 PowerShell 跑：
```powershell
curl.exe -s -X POST "https://sso.gyzq.com/auth/realms/emps/protocol/openid-connect/token" -H "Content-Type: application/x-www-form-urlencoded" -d "grant_type=password&client_id=oa-portal&username=zszx&password=Zszx@4567"
```

期望返回 JSON 包含 `access_token`。

### 4. 运行

```bash
cd C:\Users\11039\WorkBuddy\国元证券智能门户\_scripts
python sp2portal_sync.py
```

### 5. 定时任务

在门户服务器设置计划任务（每 15 分钟执行一次）：

**Windows 计划任务**：
```
触发器：每 15 分钟
操作：python C:\...\sp2portal_sync.py
```

**Linux cron**（如果门户跑在麒麟V10上）：
```cron
*/15 * * * * cd /opt/scripts && python3 sp2portal_sync.py
```

## 配置说明

### 多个新闻站点

如果想同步多个分类（如公司动态 + 部门简报），复制多份配置：

```bash
# 公司动态
python sp2portal_sync.py --config config-gsdt.yaml

# 部门简报
python sp2portal_sync.py --config config-bmjb.yaml
```

（需要先在脚本里加 --config 参数支持，当前版本固定读取 config.yaml）

### 备用：Cookie 认证

如果 Keycloak 直连不可用：
1. 浏览器登录 OA 后，导出 Cookie 到 `cookie.txt`
2. config.yaml 中 `cookie_auth.enabled: true`
