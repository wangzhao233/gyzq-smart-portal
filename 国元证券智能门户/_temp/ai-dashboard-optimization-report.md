# AI项目看板系统 优化报告

> 测试时间：2026-07-20 15:02  
> 系统地址：https://ai.wang2222.ltd  
> 版本：v2.0.0

---

## 一、CLI功能测试结果

### ✅ 通过（核心CRUD全部正常）

| # | 功能 | 方法 | 端点 | 状态 |
|---|------|------|------|------|
| 1 | 系统健康检查 | GET | `/api/health` | ✅ 200 |
| 2 | 用户登录 | POST | `/api/auth/login` | ✅ 200，JWT Token正常 |
| 3 | 获取成员列表 | GET | `/api/members` | ✅ 200，8人 |
| 4 | 获取项目列表 | GET | `/api/projects` | ✅ 200 |
| 5 | 获取项目详情 | GET | `/api/projects/{id}` | ✅ 200，含成员+角色 |
| 6 | 创建任务 | POST | `/api/tasks` | ✅ 201 |
| 7 | 更新任务状态 | PUT | `/api/tasks/{id}/status` | ✅ 200 |
| 8 | 完成任务(含说明) | PUT | `/api/tasks/{id}/status` | ✅ 200 |
| 9 | 获取任务详情 | GET | `/api/tasks/{id}` | ✅ 200 |

### ❌ 未通过

| # | 问题 | 严重级别 | 说明 |
|---|------|:--------:|------|
| 1 | **中文编码乱码** | 🔴 P0 | 所有中文字段返回乱码：`[�Ż�]` 而非 `[门户]` |
| 2 | **任务progress不更新** | 🟡 P1 | completed任务的progress仍为0 |
| 3 | **成员名称未解析** | 🟡 P1 | task.assigned_to返回member-1而非"昭哥" |
| 4 | **AI审计未触发** | 🟡 P1 | ai_audit_status始终为pending |

---

## 二、系统数据现状

### 当前用户（8人）
| ID | 姓名 | 角色 | 项目角色 |
|----|------|------|----------|
| member-1 | 昭哥(王昭) | developer | 项目经理 |
| member-2 | 张沿 | developer | 技术 |
| member-3 | 赵子健 | developer | 运维·技术负责人 |
| member-4 | 葛鹏飞(Michael) | client | 国元证券·客户 |
| member-5 | 程文斐 | client | 国元证券·元信管理员 |
| member-6 | 丁小建 | client | 国元证券·审核人 |
| member-7 | 何金钟 | client | 国元证券·批准人 |
| admin | 昭哥 | manager | — |

### 当前项目（1个）
- **国元元信一期（上线交付）** - 7名成员，0个任务（测试任务已清理）

---

## 三、优化建议（按优先级）

### 🔴 P0：修复中文编码（紧急）

**问题**：所有API响应的中文字段都是乱码

**原因**：Content-Type 头缺少 `charset=utf-8`，或数据库连接未指定UTF-8

**修复方案**：
```javascript
// 方案1：Express全局设置
app.use((req, res, next) => {
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  next();
});

// 方案2：数据库连接指定编码
// SQLite: PRAGMA encoding = "UTF-8";
// MySQL: charset=utf8mb4
```

### 🟡 P1：修复progress计算逻辑

**问题**：completed任务的progress仍为0

**修复**：
```javascript
// 任务完成时自动设置progress=100
if (status === 'completed') {
  task.progress = 100;
  task.completed_at = new Date().toISOString();
}

// 项目progress根据任务完成比例计算
const progress = Math.round((completedTasks / totalTasks) * 100);
```

### 🟡 P1：添加assigned_to名称解析

**问题**：task详情只返回member-1，不返回姓名

**修复**：
```javascript
// GET /api/tasks/:id 响应中添加assignee_name
const assignee = members.find(m => m.id === task.assigned_to);
response.assignee_name = assignee ? assignee.name : null;
```

### 🟡 P1：实现AI审计功能

**问题**：ai_audit_status始终为pending

**修复**：
```javascript
// 任务完成时触发AI审计
app.put('/api/tasks/:id/status', async (req, res) => {
  // ... 更新状态
  if (status === 'completed') {
    const audit = await runAIAudit(task);
    task.ai_audit_status = audit.status; // pass/fail
    task.ai_audit_result = audit.result;
    task.ai_audit_confidence = audit.confidence;
  }
});
```

### 🟢 P2：添加API文档

```javascript
// 安装swagger-jsdoc + swagger-ui-express
const swaggerJsdoc = require('swagger-jsdoc');
const swaggerUi = require('swagger-ui-express');

app.use('/api/docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));
```

### 🟢 P2：添加分页和过滤

```javascript
// 支持分页
GET /api/tasks?page=1&pageSize=20

// 支持状态过滤
GET /api/tasks?status=pending|in_progress|completed

// 支持负责人过滤
GET /api/tasks?assigned_to=member-1

// 支持排序
GET /api/tasks?sortBy=due_date&sortOrder=asc
```

### 🟢 P2：添加审计日志

```javascript
// 每次操作记录审计日志
POST /api/tasks/:id/status
→ 自动记录: { action: "status_change", from: "pending", to: "in_progress", by: "admin", timestamp: "..." }

// 查看审计日志
GET /api/audit?task_id={id}
```

### 🔵 P3：增强功能

1. **通知系统** - 任务分配/完成时通知相关人员
2. **文件附件** - 支持任务附件上传下载
3. **快照管理** - 项目状态备份和回滚
4. **风险管理** - AI风险识别和登记
5. **用户注册** - 开放注册或邀请制
6. **Swagger UI** - 可视化API文档

---

## 四、修复优先级

| 优先级 | 修复项 | 预计工时 |
|:------:|--------|:--------:|
| P0 | 中文编码修复 | 0.5天 |
| P1 | progress计算 | 0.5天 |
| P1 | assigned_to解析 | 0.5天 |
| P1 | AI审计功能 | 1天 |
| P2 | API文档(Swagger) | 1天 |
| P2 | 分页/过滤 | 1天 |
| P2 | 审计日志 | 1天 |
| P3 | 通知系统 | 2天 |
| P3 | 文件附件 | 2天 |

---

## 五、测试用的CLI命令参考

```bash
# 登录获取Token
TOKEN=$(curl -s -X POST "https://ai.wang2222.ltd/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"I3gRBoUgmM0J"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")

# 查看成员
curl -s -H "Authorization: Bearer $TOKEN" "https://ai.wang2222.ltd/api/members"

# 查看项目
curl -s -H "Authorization: Bearer $TOKEN" "https://ai.wang2222.ltd/api/projects"

# 查看项目详情
curl -s -H "Authorization: Bearer $TOKEN" "https://ai.wang2222.ltd/api/projects/gy"

# 创建任务
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"gy","title":"[门户] 任务标题","assigned_to":"member-1","priority":"high","due_date":"2026-07-25"}' \
  "https://ai.wang2222.ltd/api/tasks"

# 更新任务状态
curl -s -X PUT -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"in_progress"}' \
  "https://ai.wang2222.ltd/api/tasks/{TASK_ID}/status"

# 完成任务
curl -s -X PUT -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"completed","completion_note":"完成说明"}' \
  "https://ai.wang2222.ltd/api/tasks/{TASK_ID}/status"

# 删除任务
curl -s -X DELETE -H "Authorization: Bearer $TOKEN" \
  "https://ai.wang2222.ltd/api/tasks/{TASK_ID}"
```
