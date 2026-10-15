# tools/order_tools.py（替换原有文件）
import uuid
from datetime import datetime
from langchain_core.tools import tool
from database import get_db
from order_state_machine import can_transition, validate_cancel


# ==================== 菜单工具 ====================

@tool
def get_menu(category: str = "") -> str:
    """获取外卖菜单。可选传入 category 参数按分类筛选（主食/面食/特色/饮品）。
    当用户询问有哪些菜品、菜单、有什么好吃的时调用此工具。"""
    conn = get_db()
    cursor = conn.cursor()

    if category:
        cursor.execute(
            "SELECT item_id, name, price, category, stock FROM menu "
            "WHERE available=1 AND stock>0 AND category=?",
            (category,)
        )
    else:
        cursor.execute(
            "SELECT item_id, name, price, category, stock FROM menu "
            "WHERE available=1 AND stock>0 ORDER BY category, item_id"
        )

    items = cursor.fetchall()
    conn.close()

    if not items:
        return "当前菜单暂无商品，或者该分类下没有可用商品。"

    lines = ["📋 **当前菜单**\n"]
    current_cat = ""
    for item in items:
        if item["category"] != current_cat:
            current_cat = item["category"]
            lines.append(f"\n【{current_cat}】")
        stock_hint = "（库存紧张）" if item["stock"] <= 5 else ""
        lines.append(
            f"  {item['item_id']} {item['name']}  ¥{item['price']:.1f}{stock_hint}"
        )

    lines.append("\n请告诉我想点什么，可以一次点多个哦～")
    return "\n".join(lines)


# ==================== 下单工具 ====================

@tool
def create_order(items_str: str) -> str:
    """创建新订单。items_str 格式为 '商品ID:数量,商品ID:数量'，
    例如 'M001:1,M006:2'。当用户明确表示要点餐、下单、来一份等意图时调用。
    调用前请确认用户要点的商品ID和数量。"""
    # 解析商品列表
    try:
        items = []
        for pair in items_str.split(","):
            pair = pair.strip()
            item_id, qty = pair.split(":")
            items.append((item_id.strip(), int(qty.strip())))
    except Exception:
        return "下单失败：商品格式错误。请使用 '商品ID:数量' 格式，如 'M001:1,M006:2'。"

    if not items:
        return "下单失败：请至少选择一个商品。"

    conn = get_db()
    cursor = conn.cursor()

    # 校验所有商品并计算总价
    order_details = []
    total_price = 0.0
    for item_id, qty in items:
        cursor.execute(
            "SELECT name, price, stock FROM menu WHERE item_id=? AND available=1",
            (item_id,)
        )
        item = cursor.fetchone()
        if not item:
            conn.close()
            return f"下单失败：商品 {item_id} 不存在或已下架。"
        if item["stock"] < qty:
            conn.close()
            return f"下单失败：{item['name']} 库存不足（剩余 {item['stock']} 份）。"

        unit_price = item["price"]
        subtotal = unit_price * qty
        total_price += subtotal
        order_details.append({
            "item_id": item_id,
            "name": item["name"],
            "quantity": qty,
            "unit_price": unit_price,
            "subtotal": subtotal,
        })

    # 生成订单号
    order_id = f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # ← 新增

    try:
        # 插入订单主表（显式写入本地时间）
        cursor.execute(
            "INSERT INTO orders (order_id, user_id, status, total_price, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?)",
            (order_id, "user_001", "待接单", total_price, now_str, now_str)
        )

        # 插入订单明细
        for d in order_details:
            cursor.execute(
                "INSERT INTO order_items (order_id, item_id, quantity, unit_price, subtotal) "
                "VALUES (?,?,?,?,?)",
                (order_id, d["item_id"], d["quantity"], d["unit_price"], d["subtotal"])
            )
            # 扣减库存
            cursor.execute(
                "UPDATE menu SET stock = stock - ? WHERE item_id = ?",
                (d["quantity"], d["item_id"])
            )

        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return f"下单失败：系统错误 {str(e)}"
    finally:
        conn.close()

    # 构造回复
    lines = [f"✅ **下单成功！**", f"订单号：**{order_id}**", ""]
    for d in order_details:
        lines.append(f"  {d['name']} × {d['quantity']}  ¥{d['subtotal']:.1f}")
    lines.append(f"\n合计：**¥{total_price:.1f}**")
    lines.append(f"订单状态：待接单，商家正在确认中～")

    return "\n".join(lines)


# ==================== 查单工具 ====================

@tool
def check_order_status(order_id: str) -> str:
    """根据订单号查询订单状态和详情。输入订单号，如 'ORD-20261012-ABCD'。
    当用户询问订单进度、到哪了、状态时调用此工具。"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT order_id, status, total_price, created_at FROM orders WHERE order_id=?",
        (order_id,)
    )
    order = cursor.fetchone()

    if not order:
        conn.close()
        return f"未找到订单 {order_id}，请确认订单号是否正确。"

    # 查询订单明细
    cursor.execute(
        "SELECT oi.item_id, m.name, oi.quantity, oi.unit_price, oi.subtotal "
        "FROM order_items oi JOIN menu m ON oi.item_id = m.item_id "
        "WHERE oi.order_id = ?",
        (order_id,)
    )
    details = cursor.fetchall()
    conn.close()

    status = order["status"]
    lines = [f"📦 **订单 {order_id}**", f"状态：**{status}**"]

    # 根据状态给出差异化描述
    status_desc = {
        "待接单": "商家正在确认订单，预计1-2分钟内接单。",
        "备餐中": "商家已接单，正在制作中～",
        "配送中": "骑手已取餐，正在飞奔向你！",
        "已送达": "订单已送达，请查收。",
        "已取消": "订单已取消。",
        "退款中": "退款处理中，预计1-3个工作日到账。",
        "已退款": "退款已到账。",
    }
    lines.append(f"说明：{status_desc.get(status, '处理中')}")
    lines.append("")

    for d in details:
        lines.append(f"  {d['name']} × {d['quantity']}  ¥{d['subtotal']:.1f}")

    lines.append(f"\n合计：¥{order['total_price']:.1f}")
    lines.append(f"下单时间：{order['created_at']}")

    return "\n".join(lines)


# ==================== 退单工具 ====================

@tool
def process_refund(order_id: str, reason: str = "用户主动申请") -> str:
    """处理退单请求。输入订单号和退单原因。
    当用户明确表示退单、退款、取消订单时调用此工具。
    注意：配送中的订单无法取消，系统会拒绝并提示用户。"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT status, total_price FROM orders WHERE order_id=?", (order_id,))
    order = cursor.fetchone()

    if not order:
        conn.close()
        return f"订单 {order_id} 不存在，无法退单。"

    current_status = order["status"]

    # 校验是否允许取消
    allowed, reject_reason = validate_cancel(current_status)
    if not allowed:
        conn.close()
        return f"❌ 退单失败：{reject_reason}"

    # 计算退款金额
    refund_amount = order["total_price"]

    # 执行状态迁移：待接单/备餐中 → 已取消
    new_status = "已取消" if current_status in ("待接单", "备餐中") else "退款中"

    try:
        # 乐观锁：只有订单当前状态还是之前读到的值时才更新
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # ← 新增
        cursor.execute(
            "UPDATE orders SET status=?, updated_at=? "
            "WHERE order_id=? AND status=?",
            (new_status, now_str, order_id, current_status)
        )
        if cursor.rowcount == 0:
            conn.rollback()
            conn.close()
            return "退单失败：订单状态已变更（可能已被其他操作修改），请刷新后重试。"

        # 回补库存
        cursor.execute(
            "SELECT item_id, quantity FROM order_items WHERE order_id=?", (order_id,)
        )
        for row in cursor.fetchall():
            cursor.execute(
                "UPDATE menu SET stock = stock + ? WHERE item_id = ?",
                (row["quantity"], row["item_id"])
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return f"退单失败：系统错误 {str(e)}"
    finally:
        conn.close()

    return (
        f"✅ **退单已受理**\n"
        f"订单号：{order_id}\n"
        f"原状态：{current_status} → 新状态：{new_status}\n"
        f"退款金额：**¥{refund_amount:.1f}**\n"
        f"退单原因：{reason}\n"
        f"预计1-3个工作日原路退回。"
    )

# ==================== 模拟商家/骑手推进状态 ====================

@tool
def advance_order_status(order_id: str) -> str:
    """【模拟商家/骑手操作】推进订单状态到下一个阶段。
    状态链：待接单 → 备餐中 → 配送中 → 已送达。
    仅用于演示，真实系统由商家端/骑手端触发。"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT status FROM orders WHERE order_id=?", (order_id,))
    order = cursor.fetchone()
    if not order:
        conn.close()
        return f"订单 {order_id} 不存在。"

    current = order["status"]
    next_map = {
        "待接单": "备餐中",
        "备餐中": "配送中",
        "配送中": "已送达",
    }
    if current not in next_map:
        conn.close()
        return f"订单当前状态「{current}」，无法继续推进。"

    new_status = next_map[current]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "UPDATE orders SET status=?, updated_at=? WHERE order_id=? AND status=?",
        (new_status, now_str, order_id, current)
    )
    if cursor.rowcount == 0:
        conn.rollback()
        conn.close()
        return "推进失败：订单状态已变更，请刷新后重试。"

    conn.commit()
    conn.close()
    return f"✅ 订单 {order_id} 状态已推进：{current} → **{new_status}**"

# ==================== 工具导出 ====================

ALL_TOOLS = [get_menu, create_order, check_order_status, process_refund, advance_order_status]