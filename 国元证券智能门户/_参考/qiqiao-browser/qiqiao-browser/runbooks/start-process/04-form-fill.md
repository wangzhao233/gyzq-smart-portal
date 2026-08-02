# 发起流程 04：表单填写页

## 你在哪里

已从流程选择弹窗选定目标流程，经 `03-process-form.md` 打开发起流程表单弹窗并完成初始化。你可以获取字段列表、填写数据、处理子表，也可以取消关闭弹窗。

> ⚠️ **填单操作前必须读取 `core/04-field-handling.md`（字段分类与处理规则），不可跳过。**

## 本节点产出

- 表单已填写完成，用户已确认字段值，准备提交

## 可执行操作一览

| # | 操作名 | 前置条件 | 执行方式 | 下一节点 |
|---|--------|---------|---------|---------|
| 1 | 获取表单元素 | 进入表单页后首先执行 | `bsk evaluate` → `window.$ai.getFormFields()` + `window.$ai.findDom({action:'filling'})[0]` | 留在本节点 |
| 2 | 获取字段列表 | 已有表单元素 | `window.$ai.getFormFields()` 返回字段列表；`findDom({action:'filling'})[0]` 供 `__qiqiaoFormAPI` 使用 | 留在本节点 |
| 3 | 逐字段询问填值 | 字段少或用户没有现成文档 | 展示字段列表，逐个询问值 | 留在本节点 |
| 4 | 从文档提取填值 | 用户提供文档 | 读取文档→匹配字段→展示确认→填充 | 留在本节点 |
| 5 | 处理子表 | 字段列表含子表类型 | 获取子表列名→组装子表数据 | 留在本节点 |
| 6 | 执行填充 | 已有字段数据（含子表数据） | `bsk evaluate` → `window.$ai.fillingForm()` | 留在本节点 |
| 7 | 提交前检查 | 已执行填充 | 必填校验 + 联动新增字段检查 | 留在本节点 |
| 8 | 文件上传 | 有上传字段 + 用户提供本地文件 | `bsk evaluate` + DataTransfer | 留在本节点 |
| 9 | 提交 | 已填写完成 | 展示已填值→用户确认→`bsk click @eN` | 见下方 |
| 10 | 取消 | 用户不想继续填单 | 关闭表单弹窗 | → `03-process-form.md` |
| 11 | 弹窗选择类字段 | 地址/级联/外键/关联等字段 | 见 `04-field-handling.md` §B | 留在本节点 |

---

### 操作 1：获取表单元素和字段

**第一步：滚动表单到底部，加载全部字段（必做）**

打开表单弹窗后，必须先将表单内容滚动到底部，触发延迟渲染的字段加载完成，然后才能获取字段。

```
bsk evaluate "document.querySelector('.process_content .drawer_content').scrollTo({ top: document.querySelector('.process_content .drawer_content').scrollHeight, behavior: 'smooth' })"
```

> 滚动容器为 `.drawer_content`，通过父级 `.process_content` 精确定位。

**第二步：初始化并获取字段和表单元素**

形式化执行：

```
bsk evaluate → window.$ai.init()
bsk evaluate → window.$ai.getFormFields()  → 字段列表
bsk evaluate → window.$ai.findDom({ action: 'filling' })[0]  → 拿到 elementData
```

这是后续所有操作的基础，**必须先完成**。拿不到 elementData 说明表单未正确打开，退回 `03-process-form.md`。

> ⚠️ **注意**：`window.$ai.init()` 后 `getFormFields()` 和 `findDom({action:'filling'})[0]` 应能获取到字段和表单元素。若两者均返回空，检查是否已执行 `init()`、弹窗是否已完全加载。

### 操作 2：获取字段列表

**获取字段的标准顺序（必须遵守）：**

1. **`window.$ai.getFormFields()`** — 首选，返回所有字段信息 ✅
2. **`window.$ai.findDom({action:'filling'})[0]`** — 获取表单元素引用，供 `__qiqiaoFormAPI` 函数使用
3. 如果上述两个 API 均无返回数据 → **降级用 `bsk snapshot`**

字段列表中包含所有可填字段的名称（`name`）和类型（`type`）。按 `core/04-field-handling.md` §1 中的 A~E 分类处理每个字段。

`bsk snapshot` 仅用于**验证**（确认表单已加载、按钮位置等），不用于获取字段列表。

展示字段给用户时，**按字段在表单中的自然顺序排列**，标注需要用户关注的字段：
- 普通字段：直接展示字段名和类型
- 需弹窗选择的字段（地址/级联/外键/关联）：AI 点击勾选
- 需上传文件的字段：提供本地文件地址，或在线文件链接
- 需手动操作的字段：展示给用户看，需要手动操作

### 操作 3：逐字段询问填值

将字段列表展示给用户，逐个询问每个字段的值。适用于字段少或用户没有现成文档的场景。

不同类别的字段处理方式不同：
- **A 类**：直接问值，准备传给 `fillingForm`
- **B 类**：问值后走 bsk 点击选择（见 `04-field-handling.md` §B）
- **D 类**：标注「需手动操作」，不问值
- **C 类**（文件上传）：问文件路径或 URL

### 操作 4：从文档提取填值

用户提供文档时：

1. 读取文档内容，提取与表单字段匹配的值
2. 将匹配结果展示给用户确认
3. 用户确认后按顺序执行：操作 5（子表）→ 操作 6（填充）→ 操作 7（检查）→ 操作 8（文件上传）
4. 未匹配的字段回退到操作 3，向用户询问

### 操作 5：处理子表

这是最复杂的部分。`getFormFields()` 的字段列表中可以看到子表字段，但**看不到子表的列名**。

#### 5.1 获取子表列名

通过 Vue 内部 API 获取子表及列名（使用 `findDom({action:'filling'})[0]` 拿到的 elementData）：

```
elementData.__qiqiaoFormAPI.getFormInfoData().fields
  → 筛选 type === "subform" 的字段
    → 每个子表的 subForms 属性中，取 permission === "MODIFY" 的 title
```

> ⚠️ **禁止用"添加一行"方式获取列名**——会创建空白行污染表单。
> ⚠️ 如果 Vue API 获取失败，直接询问用户子表有哪些列。

#### 5.2 子表数据填充

拿到列名后，组装 data 对象传给 `fillingForm`：

```js
{
  "子表字段名": [
    { "列名1": "值1", "列名2": "值2" },
    { "列名1": "值3", "列名2": "值4" }
  ]
}
```

**行为约束：**
- `fillingForm` 对子表是**追加行**，不是更新。禁止对同一子表重复调用
- 所有日期/时间值必须转成正确格式（`2026-07-10`、`14:30`）

### 操作 6：执行填充

调用前必须先完成子表处理（操作 5）。

组装所有 A 类字段的值（加上子表数据），统一传给 `fillingForm`：

```
bsk evaluate → window.$ai.fillingForm(elementData, data)
```

> `fillingForm` 处理普通字段 + 子表 + 上传字段（URL），不处理 B 类选择字段和本地文件上传。

### 操作 7：提交前检查

填充完成后**必须执行**，包含两个检查项。

#### 检查 1：必填项校验

1. 通过 Vue API 获取字段完整信息，筛选 `required === true` 的必填字段
2. 对比已填充的值，找出为空的必填字段
3. 有空值时，根据已有信息尝试补填，或询问用户
4. 确认后 `fillingForm` 补填

#### 检查 2：联动/条件新增字段

1. 再次 `window.$ai.getMetadata(elementData)` 获取当前实际显示的字段
2. 与操作 2 的字段列表对比，找出新增字段
3. 新增字段有空值时，询问用户 → `fillingForm` 补填

### 操作 8：文件上传

**仅当用户提供本地文件路径时执行。** 用户提供 URL 的，走 `fillingForm` 即可。

流程：
1. 读取文件转 base64
2. 用 `bsk evaluate` 构造 Blob→File，通过 DataTransfer 设置到 `input[type=file]`
3. dispatch change 事件触发上传
4. `bsk snapshot` 确认上传成功

> 具体细节见 `core/04-field-handling.md` §C。

### 操作 9：提交

> ⚠️ **严禁未经用户确认自动提交。**

1. 展示已填写的所有字段值，让用户核对
2. 询问提交方式：保存并继续添加 / 直接提交
3. 用户确认后：`bsk click @eN` 点击提交/保存按钮
4. **执行结果检测（见 GR-08）：** 点击后 2 秒、5 秒各做一次 `bsk snapshot`
   - 页面变化 → 按下一节点继续
   - 页面无变化 + 有 3 秒提示消息 → 已捕捉到，正常继续
   - 页面无变化 + 无提示 → `bsk evaluate` 查看接口返回值获取错误信息，告知用户

**提交后去向：**

| 流程类型 | 下一节点 |
|----------|---------|
| 发起流程 | → `05-post-action.md`（选人/意见弹窗） |

> 发起流程场景的提交流程为：`bsk click @eN 提交` → `05-post-action.md` 选人弹窗（搜索+选人+确定）→ 办理弹窗（再确定）→ 完成。

### 操作 10：取消

关闭表单弹窗，返回 `03-process-form.md`。先看有没有「取 消」按钮，没有则用 `i.iconclose`。

### 操作 11：弹窗选择类字段

地址选择器、级联选择、外键选择、子表关联、多表关联等字段的 B 类操作，统一遵循以下模式：

```
bsk click @eN 触发按钮 → 弹窗打开
bsk snapshot 查看弹窗内容 → 展示给用户
bsk click @eN 选择数据 → 确定
bsk click @eN "确 定" → 完成
```

关闭弹窗优先用「取 消」按钮，不要一上来就用 `i.iconclose`。不同字段的具体流程见 `core/04-field-handling.md` §B。

---

## 操作失败处理

| 失败场景 | 处理方式 | 回退 |
|----------|---------|------|
| `findDom({action:'filling'})` 返回空 | 表单未正确打开，检查页面状态 | → `03-process-form.md` |
| `getFormFields` 返回 null | 降级 `bsk snapshot` | 留本节点 |
| `fillingForm` 返回 false | 检查 key 是否为中文字段名；检查值类型；尝试逐字段填充 | 留本节点 |
| 子表出现重复行 | `fillingForm` 对子表是追加行为，禁止重复调用 | 留本节点 |
| 子弹窗找不到「取 消」/「确 定」 | 询问用户按钮位置 | 留本节点 |

## 下一节点

操作 9 成功 → **`05-post-action.md`（选人/意见弹窗）**
操作 10 → **`03-process-form.md`（表单弹窗）**
