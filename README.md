# 🐼🐻 一二布布外卖客服 Agent

基于 **LangGraph + 通义千问** 的双 Agent 外卖客服系统。以「一二」（白熊猫）和「布布」（棕小熊）两个卡通角色，模拟真实外卖场景下的用户端交互：**菜单查询、下单、查单、退单**，并内置 **HITL 确认、订单状态机、乐观锁** 等生产级机制。

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| **双 Agent 角色化协作** | 一二（前台客服）负责菜单、下单、查单、安抚情绪；布布（后台处理）负责退单、退款。通过 Supervisor 节点智能路由。 |
| **HITL 确认机制** | 下单和退单前暂停执行，返回订单明细让用户二次确认，避免 LLM 误解意图导致误操作。 |
| **订单状态机** | 7 个状态的迁移矩阵（待接单 / 备餐中 / 配送中 / 已送达 / 已取消 / 退款中 / 已退款），非法迁移直接拒绝。 |
| **模拟商家推进** | 一键推进订单状态（待接单 → 备餐中 → 配送中 → 已送达），完整演示订单生命周期。 |
| **乐观锁防并发** | 订单状态更新时检查状态是否仍为预期值，防止并发冲突导致库存回补两次。 |
| **混合格式输入解析** | 支持 `M001 1份`、`一份M001`、`M001:1`、`我要一份M005和M006两份` 等多种写法。 |
| **粉色 Gradio 界面** | 一二布布头像、消息气泡、一键快捷按钮（查看菜单 / 我要点餐 / 查订单 / 模拟商家推进）。 |

## 🛠 技术栈

| 类别 | 内容 |
|------|------|
| **语言** | Python 3.12 |
| **大模型** | 通义千问 `qwen3.8-flash` |
| **Agent 框架** | LangChain、LangGraph |
| **Web 框架** | Gradio（聊天界面）+ FastAPI（API 入口） |
| **数据库** | SQLite（`waimai.db`） |
| **状态管理** | 自定义 `pending_actions` 内存字典 |
| **其他** | python-dotenv、Pillow |

## 📁 项目结构

```text
yier-bubu-agent/
├── agents/
│   ├── supervisor.py          # 调度中心：根据意图路由到一二 / 布布
│   ├── yier_agent.py          # 一二：菜单查询、下单、查单
│   └── bubu_agent.py          # 布布：退单、退款
├── tools/
│   └── order_tools.py         # 工具集：get_menu / create_order / check_order_status / process_refund / advance_order_status
├── assets/                    # 一二、布布头像
├── app.py                     # Gradio 聊天界面
├── main.py                    # FastAPI 入口（提供 /chat 接口）
├── graph_workflow.py          # LangGraph 状态图编排
├── config.py                  # 角色 Prompt 配置
├── database.py                # SQLite 初始化与连接
├── order_state_machine.py     # 订单状态机与迁移矩阵
├── pending_actions.py         # HITL 待确认操作存储
├── waimai.db                  # SQLite 数据库（含菜单初始数据）
├── requirements.txt
└── .env                       # 环境变量（不提交）
```

---

## 🚀 本地运行

### 1. 克隆项目并安装依赖

```bash
git clone https://github.com/L-GF182/yier-bubu-agent.git
cd yier-bubu-agent
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

### 2. 配置环境变量

在项目根目录创建 .env 文件：

```env
OPENAI_API_KEY=sk-你的通义千问API密钥
OPENAI_BASE_URL=https://你的专属地址/compatible-mode/v1
```

### 3. 启动 Gradio 聊天界面

```bash
python app.py
```
浏览器打开 http://127.0.0.1:7860。

### 4. （可选）启动 FastAPI 服务

```bash
uvicorn main:app --reload
```
访问 http://127.0.0.1:8000/docs 查看 API 文档。

## 📡 API 示例

```bash
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "我要一份M001和M006两份"}'
```

---

## 🎬 演示流程

| 步骤 | 输入 | 预期效果 |
|---|------|---------------------|
| 1 | 有什么吃的 | 列出 6 个菜单商品 |
| 2 | 我要点 M001 1份 | 一二返回确认提示（HITL） |
| 3 | 确认 | 下单成功，生成订单号 |
| 4 | 我的订单ORD-xxx到哪了 | 显示"待接单"状态 |
| 5 | 点击【⏩ 模拟商家推进】 | 状态 → 备餐中 |
| 6 | 点击【⏩ 模拟商家推进】 | 状态 → 配送中 |
| 7 | 帮我退了ORD-xxx → 确认 | ❌ 被拒绝（配送中不可退，状态机拦截） |
| 8 | 点击【⏩ 模拟商家推进】 | 状态 → 已送达 |

---

## 🔒 生产级设计

| 机制 | 解决的问题 |
|------|------|
| HITL 确认 | 防止 LLM 误解意图导致误下单 / 误退单 |
| 订单状态机 | 配送中订单不允许取消，符合真实业务规则 |
| 乐观锁 | 防止两个请求同时退单导致库存回补两次 |
| 纯 LLM 路由 | 区分"取消订单"（执行）和"取消订单后有什么影响"（咨询） |

---

## ❓ 常见问题 FAQ

<details>
<summary>👉 点击查看常见报错</summary>

**Q：大模型返回报错 401 Unauthorized**
- 检查 `.env` 的 `OPENAI_API_KEY`、`OPENAI_BASE_URL` 是否填写正确，注意不要多余空格或换行。

**Q：Gradio 页面打不开**
- 确认 `python app.py` 启动无报错，默认访问地址：`127.0.0.1:7860`。

**Q：订单查询报错，数据库异常**
- 如果 `waimai.db` 文件损坏，可以直接删除，程序启动时会自动重建并初始化菜单数据。

</details>

## 📄 License
MIT