# agents/yier_agent.py
import os
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config import YIER_PROMPT
from tools.order_tools import get_menu, create_order, check_order_status
from pending_actions import set_pending, get_pending, clear_pending, is_confirmation, is_cancellation

load_dotenv()

llm = ChatOpenAI(
    temperature=0.3,
    model="qwen3.8-flash",
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    openai_api_base=os.getenv("OPENAI_BASE_URL"),
)


def _parse_order_items(question: str) -> str | None:
    """解析用户输入中的商品ID和数量（支持混合格式）"""
    # 统一 O → 0
    question = question.replace("O", "0").replace("o", "0")

    cn_num = {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5,
              "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}

    # 优先级最高：M001:1 或 M001：1
    pattern1 = re.findall(r"(M\d{3,})\s*[:：]\s*(\d+)", question)
    if pattern1:
        return ",".join(f"{i}:{q}" for i, q in pattern1)

    results = []
    consumed = set()  # 记录已经匹配过的 Mxxx 起始位置，避免重复

    # 模式A：数量 + 单位 + ID（如"一份M005"）
    for m in re.finditer(r"(\d+|[一二三四五六七八九十两]+)\s*[份个杯碗]\s*(M\d{3,})", question):
        qty_str, item_id = m.group(1), m.group(2)
        qty = int(qty_str) if qty_str.isdigit() else cn_num.get(qty_str, 1)
        results.append((item_id, qty))
        consumed.add(m.start(2))

    # 模式B：ID + 空格 + 数字（如"M005 2"）
    for m in re.finditer(r"(M\d{3,})\s+(\d+)\s*[份个杯碗]?", question):
        if m.start(1) in consumed:
            continue
        item_id, qty = m.group(1), int(m.group(2))
        results.append((item_id, qty))
        consumed.add(m.start(1))

    # 模式C：ID + 中文数字 + 单位（如"M006两份"）
    for m in re.finditer(r"(M\d{3,})\s*([一二三四五六七八九十两]+)\s*[份个杯碗]", question):
        if m.start(1) in consumed:
            continue
        item_id, qty_str = m.group(1), m.group(2)
        qty = cn_num.get(qty_str, 1)
        results.append((item_id, qty))
        consumed.add(m.start(1))

    # 模式D：独立的 ID（没有任何数量信息，默认数量 1）
    for m in re.finditer(r"(M\d{3,})", question):
        if m.start(1) in consumed:
            continue
        results.append((m.group(1), 1))
        consumed.add(m.start(1))

    if not results:
        return None

    # 去重：同一个 ID 只保留第一次出现
    seen = {}
    for item_id, qty in results:
        if item_id not in seen:
            seen[item_id] = qty

    return ",".join(f"{i}:{q}" for i, q in seen.items())


def _format_order_summary(items_str: str) -> str:
    """把 'M001:1,M006:2' 格式化为人类可读的摘要"""
    from database import get_db
    conn = get_db()
    cursor = conn.cursor()
    lines = []
    total = 0.0
    for pair in items_str.split(","):
        item_id, qty = pair.split(":")
        cursor.execute("SELECT name, price FROM menu WHERE item_id=?", (item_id,))
        row = cursor.fetchone()
        if row:
            subtotal = row["price"] * int(qty)
            total += subtotal
            lines.append(f"  {row['name']} × {qty}  ¥{subtotal:.1f}")
    conn.close()
    lines.append(f"\n合计：¥{total:.1f}")
    return "\n".join(lines)


def yier_respond(question: str, session_id: str = "default") -> str:
    """一二回复：菜单查询 + 下单 + 查订单状态 + 撒娇语气"""

    # ========== 0. 检查待确认操作（HITL） ==========
    pending = get_pending(session_id)
    if pending and pending["agent"] == "yier":
        if is_confirmation(question):
            clear_pending(session_id)
            result = create_order.invoke(pending["params"])
            return f"好哒！一二帮你下单啦～\n\n{result}"
        elif is_cancellation(question):
            clear_pending(session_id)
            return "好哒～一二已经帮你取消啦，还有其他需要吗？"
        else:
            # 用户说了别的话，清除 pending，继续正常流程
            clear_pending(session_id)

    # ========== 1. 查订单状态（最高优先级） ==========
    order_match = re.search(r"ORD-[\dA-Z-]+", question)
    if order_match:
        order_id = order_match.group()
        result = check_order_status.invoke({"order_id": order_id})
        return f"一二帮你查了一下～\n{result}"

    # ========== 1.1 模拟商家推进订单状态（演示用） ==========
    advance_match = re.search(r"推进\s*(ORD-[\dA-Z-]+)", question)
    if advance_match:
        from tools.order_tools import advance_order_status
        order_id = advance_match.group(1)
        result = advance_order_status.invoke({"order_id": order_id})
        return f"【系统模拟商家操作】\n{result}"

    # ========== 2. 下单意图检测 ==========
    # 先尝试解析商品，能解析出来就说明用户要点餐（不管有没有"下单"关键词）
    items_str = _parse_order_items(question)

    # 如果没解析出商品，再看有没有下单关键词，决定是否提示"请告诉商品ID"
    order_intent_keywords = ["下单", "点餐", "来一份", "来一个", "点一份", "帮我点", "我要点"]
    has_order_intent = any(kw in question for kw in order_intent_keywords)

    if items_str:
        # 能解析出商品 → 走 HITL 确认
        summary = _format_order_summary(items_str)
        set_pending(
            session_id=session_id,
            agent="yier",
            action="create_order",
            params={"items_str": items_str},
            summary=summary,
        )
        return (
            f"一二确认一下～你要点的是：\n\n{summary}\n\n"
            f"确认下单吗？回复「确认」一二就帮你下单～"
        )
    elif has_order_intent:
        # 有下单意图但没解析出商品 → 提示用户给出商品ID
        return ("呜呜，一二没有听清你要点什么。请告诉一二【商品ID】和【数量】，"
                "比如「M005 2份」哦～你可以先点上面的【查看菜单】按钮看看有哪些好吃的！")
    # ========== 3. 菜单查询 ==========
    menu_keywords = ["菜单", "有什么吃", "有哪些", "看看菜", "有什么菜", "点餐"]
    if any(kw in question for kw in menu_keywords):
        result = get_menu.invoke({"category": ""})
        return f"一二来给你看看菜单～\n\n{result}"

    # ========== 4. 兜底：交给 LLM ==========
    response = llm.invoke([
        SystemMessage(content=YIER_PROMPT),
        HumanMessage(content=question),
    ])
    return response.content