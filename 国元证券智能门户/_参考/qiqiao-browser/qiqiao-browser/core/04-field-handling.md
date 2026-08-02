# 字段分类与处理规则（AI操作指南）

> **读取阶段：** 阶段三（主会话进入表单填写节点前必读）
>
> 本文档定义填单时所有字段类型的分类和处理方式。主会话执行到表单填写页面时**必须读取本文档**。

## 核心原则

| 处理方式 | 适用字段 | 说明 |
|---------|---------|------|
| **`window.$ai.getFormFields()`** | 所有字段（填单/发起流程/审批弹窗通用） | 优先获取完整字段列表 |
| **`window.$ai.findDom({action:'filling'})[0]`** | 表单容器元素引用 | 供 `__qiqiaoFormAPI` 函数使用 |
| **`window.$ai.fillingForm` 批量填充** | 普通字段、时间字段、上传字段(URL) | 一次调用填所有普通字段 |
| **`bsk click @eN` 点击选择** | 地址/级联/人员/部门/外键/关联弹窗 | 通过 snapshot 定位 @eN 后点击 |
| **`bsk fill @eN --value "x"`** | 详细地址、文本输入 | snapshot 定位后直接填值 |
| **`bsk evaluate` + DataTransfer** | 本地文件上传 | 读取文件→base64→Blob→File→input |
| **`bsk snapshot`** ⚠️ | 兜底降级 | 以上 API 均无返回数据时使用，不可作为首选 |

---

## §1 字段分类总览

通过 `window.$ai.getFormFields()` 获取字段列表后，按以下分类处理。

### A — `window.$ai.fillingForm` 直接填充（最常用）

这些字段类型全部走 `window.$ai.fillingForm`，一次性传入所有字段的值：

| type | name 示例 | 值格式 |
|------|----------|--------|
| `textBox` | 单行文本1 | 字符串 |
| `textarea` | 多行文本1 | 字符串，支持换行 |
| `number` | 数字1 | 数字或数字字符串 |
| `singleSelect` | 单项选择1 | 选项文本（如"选项A"） |
| `multiSelect` | 多项选择1 | 数组（如 `["A","B"]`） |
| `editor` | 富文本1 | HTML 字符串 |
| `singleUserSelect` | 人员单选1 | 人员姓名 |
| `multiUserSelect` | 人员多选1 | 姓名数组 |
| `singleDepartmentSelect` | 部门单选1 | 部门名称 |
| `multiDepartmentSelect` | 部门多选1 | 部门名称数组 |
| `rated` | 评分1 | 数字（1-5） |
| `foreignSelection` | 外键选择1 | 外键值（如有） |
| `date` | 日期1 | `2026-07-10` |
| `time` | 时间1 | `14:30` |
| `datetime` | 日期时间1 | `2026-07-10 14:30:00` |
| `imageUpload` | 图片上传1 | URL 字符串（仅限在线链接） |
| `fileupload` | 文件上传1 | URL 字符串（仅限在线链接） |
| `audio` | 音频1 | URL 字符串 |
| `video` | 视频1 | URL 字符串 |
| `subform` | 子表单1 | 对象数组 `[{列名:值}]`（见下方子表说明） |

**操作步骤：**
```
1. bsk evaluate → window.$ai.getFormFields() 获取字段列表
2. 展示字段给用户，收集值
3. 组装 data 对象（字段名为 key）
4. bsk evaluate → window.$ai.fillingForm(elementData, data)
```

### 子表列名获取（关键）

`getFormFields()` 返回的字段列表中不包含子表的列名。需要通过 Vue 内部 API 获取（使用 `findDom({action:'filling'})[0]` 拿到的 elementData）：

```js
// 通过 elementData 获取完整字段数据
const inputs = elementData.__qiqiaoFormAPI.getFormInfoData().fields;
// 筛选 type === "subform" 的字段（即子表）
const subForms = inputs.filter(f => f.type === 'subform');
// 对每个子表，从 subForms 中筛选 permission === "MODIFY" 的列，提取 title
subForms.forEach(sf => {
  const columns = sf.subForms
    .filter(col => col.permission === 'MODIFY')
    .map(col => col.title);
  // columns 即为该子表的可填写列名数组
  // 例：["公司名称", "职位名称", "入职时间", "离职时间", "工作内容"]
});
```

> ⚠️ **禁止用"添加一行"方式获取列名**——会创建空白行污染表单。
> ⚠️ 如果 Vue API 获取失败，询问用户该子表有哪些列。

### 子表数据填充

拿到列名后，组装 data 对象传给 `fillingForm`：

```js
// 子表字段的值必须为对象数组
{
  "普通字段": "值",
  "工作经历": [      // 子表字段名（来自 getFormFields）
    { "公司名称": "腾讯", "职位名称": "产品经理" },  // key 为列名（title）
    { "公司名称": "阿里", "职位名称": "设计师" }
  ]
}
```

**子表行为约束：**
- **追加行，不更新**：`fillingForm` 对子表会新增行，不会匹配或覆盖已有行。**禁止对同一子表重复调用**，否则产生重复行。

> 日期格式严格使用 `-` 分隔：`2026-07-10`、`14:30`、`2026-07-10 14:30:00`

---

### B — `bsk click @eN` 逐级选择

这些字段无法用 `fillingForm` 填充，需要通过 `bsk snapshot` 定位元素后点击操作。

#### B1 — 地址选择器（address）

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | `bsk click @eN` textbox "请选择" | 弹出省份列表 |
| 2 | `bsk click @eN` 省份名（如"广东省"） | 弹出城市列表 |
| 3 | `bsk click @eN` 城市名（如"广州市"） | 弹出区级列表 |
| 4 | `bsk click @eN` 区名（如"天河区"） | ✅ 值填入 `广东省 / 广州市 / 天河区` |
| 5 | `bsk fill @eN --value "详细地址"` | 填入详细地址 |

> 省市区是三级 cascading menu，每选一级出下一级。最终值格式为 `省 / 市 / 区`。

#### B2 — 级联选择（cascadeSelection）

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | `bsk click @eN` textbox "请选择" | 弹出第一级列表 |
| 2 | `bsk click @eN` 选项（如"华南"） | 弹出第二级列表 |
| 3 | `bsk click @eN` 选项（如"广东"） | ✅ 值填入 `华南 / 广东` |

> 与地址选择器交互模式相同，`bsk click` 逐级选择到底。

#### B3 — 人员/部门选择

> ✅ **直接用 `fillingForm` 填写，不用打开弹窗选择。** 人员单选/人员多选/部门单选/部门多选支持 `fillingForm` 直接传值（用户的姓名/部门名），无需走弹窗选择流程。

**方式一（用户给了姓名/部门名）：**

```
bsk evaluate → window.$ai.fillingForm(element, {
  "人员单选1": "张三",
  "人员多选1": ["张三", "李四"],
  "部门单选1": "技术部",
  "部门多选1": ["技术部", "产品部"]
})
```

- 字符串 = 单选（单值）
- 数组 = 多选（多值）
- 平台会自动匹配最接近的姓名/部门

**方式二（用户未提供，弹窗选择）：**

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | `bsk click @eN "选择"` | 打开选择弹窗 |
| 2 | 搜索：`bsk fill @eN 搜索框 --value "姓名"` | 缩小范围 |
| 3 | 或点击 Tab 切换（常用/部门成员/全部成员） | 切换列表 |
| 4 | `bsk click @eN` 目标人员/部门（checkbox） | 勾选 |
| 5 | `bsk click @eN "确 定"` | ✅ 值填入表单 |

> 人员弹窗标题「人员列表」，部门弹窗标题「部门列表」。关闭优先用「取 消」按钮。
> **优先方式一**：直接 `fillingForm` 传姓名/部门名，更快更准，无需走弹窗。

#### B4 — 外键选择（foreignSelection）

当用户**未提供外键值**时：

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | `bsk evaluate` 点击 `.custom_icon.iconfont.iconicon-amplification` | 打开「选择内容」弹窗 |
| 2 | `bsk snapshot` 查看弹窗内数据列表 | 展示给用户选择 |
| 3 | `bsk click @eN` 目标数据行（如"鼠标"） | 选中 |
| 4 | `bsk click @eN "确 定"` | ✅ 值填入，关联字段自动回显 |

> 外键弹窗为单选。用户已提供外键值时直接走 `fillingForm`。

#### B5 — 子表关联

> ⚠️ **严重警告：严禁使用 `window.$ai.fillingForm` 填充子表关联数据！** 子表关联数据必须通过弹窗勾选 checkbox 选择，`fillingForm` 无法正确处理子表关联的关联关系，填入后会导致**最严重的数据错误**（关联关系断裂、数据丢失）。

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | `bsk click @eN "添加"` 或 `window.$ai.findDom({id:'__canEdit'})` | 打开「批量管理」弹窗 |
| 2 | `bsk snapshot` 查看数据列表 | 展示给用户选择 |
| 3 | 勾选目标数据行 checkbox（见下方说明） | 点 checkbox，不要点行文本 |
| 4 | `bsk click @eN "确 定"` | ✅ 数据关联到子表 |

> 子表关联弹窗分上下两部分：上=数据列表，下=已添加数据。可多选。
> **必须通过弹窗 checkbox 勾选数据。** 禁止使用 `fillingForm` 或任何 JS 直接赋值方式处理子表关联字段。

#### B6 — 多表关联

> ⚠️ **严重警告：严禁使用 `window.$ai.fillingForm` 填充多表关联数据！** 与子表关联同理，多表关联数据必须通过弹窗勾选 checkbox 操作，`fillingForm` 直接填充会破坏关联关系，导致**数据错误且无法恢复**。

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | `bsk click @eN "批量管理"` | 打开「批量管理」弹窗（标题「选择关联表数据」） |
| 2 | `bsk snapshot` 查看数据列表 | 展示给用户选择 |
| 3 | 勾选目标数据行 checkbox（见下方说明） | 点 checkbox，不要点行文本 |
| 4 | `bsk click @eN "确 定"` | ✅ 数据关联到多表 |

> 弹窗有搜索和「仅展示关联表」切换开关。
> **必须通过弹窗 checkbox 勾选数据。** 禁止使用 `fillingForm` 或任何 JS 直接赋值方式处理多表关联字段。

#### 勾选表格行 checkbox 的正确方法（通用规则）

> ⚠️ **关键：点击数据行本身不会选中复选框！** 只能通过 `bsk snapshot` 精准定位到行内 checkbox 并点击。
>
> 在所有表格（vxe-table、el-table）中勾选数据行时，**不能**直接点击行文本或行区域——这不会触发 checkbox 的选中状态。
>
> 也不要用 `querySelector('input[type=checkbox]')` 无差别选择——表格 DOM 结构是**表头（含全选 checkbox）在前 → 数据行 checkbox 在后**，`querySelector` 会先命中表头全选框。
>
> 适用场景：子表关联数据选择、多表关联数据选择、列表删除勾选、列表批量操作勾选等所有表格行勾选操作。

**唯一正确方式：`bsk snapshot` 定位 checkbox @eN + `bsk click @eN`**

```
# 先 snapshot，找到目标行 checkbox 的 ref
bsk snapshot --session xxxx

# 直接 click 那个 checkbox 的 @eN
bsk click --session xxxx @eN
```

**定位口诀：** 用 snapshot 找到目标行前面的 checkbox 元素（不是行文本，不是表头全选框），拿到它的 @eN，然后 click。

---

### C — 本地文件上传

当用户提供**本地文件路径**时（URL 直接走 fillingForm）：

| 步骤 | 操作 |
|------|------|
| 1 | 读取文件 → base64 编码 |
| 2 | 构造 File 对象：`atob()` → `Uint8Array` → `Blob` → `File` |
| 3 | 用 DataTransfer 设置到 `input[type=file]` |
| 4 | `dispatchEvent(new Event("change"))` 触发上传 |
| 5 | `bsk snapshot` 确认文件已上传 |

> 不同上传字段的 file input 索引不同，用 `bsk evaluate` 通过 `querySelector` 定位目标上传区域的 `<input type=file>`。上传到错误索引会弹出格式限制提示。

---

### D — 需手动操作的字段

以下字段**不填充、不询问用户值**，但在展示字段列表时标注「需手动操作」：

| type | name 示例 | 说明 |
|------|----------|------|
| `location` | 地理位置1 | 地理位置信息 |
| `summary` | 汇总1 | 汇总字段 |
| `handwriting` | 手写签名1 | 手写签名 |
| `onlineEdit` | 在线编辑1 | 在线编辑 |
| `relationQuery` | 关联查询1 | 关联查询 |
| `aggregateQuery` | 聚合查询1 | 聚合查询 |
| `aiDialog` | 智能对话框1 | 智能对话框 |
| `aiDisplay` | 智能回显1 | 智能回显 |
| `aiButton` | 智能按钮1 | 智能按钮 |
| `generateCode` | 生成编码1 | 系统自动生成 |

---

### E — 分步操作按钮

这些不是表单字段，是独立操作按钮，不走 `fillingForm`：

| 按钮 | 操作方式 | 说明 |
|------|---------|------|
| 子表「添加一行」 | `bsk click @eN` | 直接添加空白行 |
| 子表「添加」（关联） | `bsk click @eN` → 弹窗选择 | 见 B5 子表关联 |
| 多表「批量管理」 | `bsk click @eN` → 弹窗选择 | 见 B6 多表关联 |
| 「拍照」/「选取文件」 | 本地文件上传 | 见 C |
| 「提交」 | `bsk click @eN` | 需用户确认后点击 |
| 「保存并继续添加」 | `bsk click @eN` | 保存不关闭表单 |

#### 行操作按钮（子表/子表关联/多表关联）

子表、子表关联、多表关联的表格中，每行都有操作按钮，可通过 `$ai` 元数据定位：

| 元数据 id | 名称 | type | 用途 |
|-----------|------|------|------|
| `__canViewForm` | 查看 | `formDetail` | 查看该行表单数据 |
| `__canEdit` | 编辑 | `formEdit` | 编辑该行关联表数据 |
| `more` | 更多操作 | `null` | 展开更多行操作 |
| `__canDel` | 删除 | `formDel` | 删除该行关联表数据 |
| `__canCopy` | 复制 | `formCopy` | 复制该行关联表数据 |

**操作方式（优先用 $ai 定位具体行，降级用 bsk）：**

```
方式一（优先）：window.$ai.findDom({id:'__canEdit'})[0]?.click()
  → $ai 按 id 精确定位到第 1 行的编辑按钮

方式二（降级）：bsk snapshot → 找到第 N 行的编辑按钮 @eN
  → bsk click @eN
```

> 如需操作**特定行**（比如第 3 行），`window.$ai.findDom({id: '__canEdit'})` 返回的是匹配 id 的按钮数组，索引从 0 开始对应第 1 行。取 `[N-1]` 即第 N 行的按钮。
>
> 如果 `window.$ai.findDom` 找不到（如 DOM 未渲染完成），降级用 `bsk snapshot` 找到对应行的按钮 ref 再 `bsk click @eN`。

---

## §2 弹窗关闭规则

| 场景 | 操作 | 优先级 |
|------|------|--------|
| 子弹窗（人员/部门/外键/关联选择） | `bsk click @eN "取 消"` | 优先 |
| 子弹窗无「取 消」按钮 | `bsk click @eN Close` 图标 | 其次 |
| 主表单 dialog | `bsk evaluate 'i.iconclose?.click()'` | 最后 |

> **注意：** 先检查弹窗内是否有「取 消」按钮，有则优先用它关闭，不要一上来就用 `i.iconclose`，否则可能误关主表单。

---

## §3 填单完整流程

```
1. bsk snapshot → 确认在表单填写页
2. bsk evaluate → window.$ai.init() 初始化
3. bsk evaluate → window.$ai.getFormFields() 获取所有字段列表
4. bsk evaluate → window.$ai.findDom({action:"filling"})[0] 获取表单元素引用（供 __qiqiaoFormAPI 使用）
5. 如果步骤 3/4 均无返回数据 → 降级用 bsk snapshot
6. 按 §1 分类处理每个字段：
   ├─ A类（普通/时间/上传URL）→ 组装 data → window.$ai.fillingForm()
   ├─ B类（地址/级联/人员/外键）→ bsk click 逐级/弹窗操作
   ├─ B5/B6（子表关联/多表关联）→ ⚠️ **必须走弹窗 checkbox 选择，禁止 fillingForm！**
   ├─ C类（本地文件）→ DataTransfer 上传
   └─ D类（跳过）→ 标注「需手动操作」
7. bsk snapshot → 确认已填值
8. 展示已填字段给用户核对
9. 用户确认后 → bsk click @eN 提交/保存
```
