"""订单状态机——定义合法的状态迁移"""
ORDER_STATUS = {
    "待接单": "PENDING",       # 用户已下单，等待商家确认
    "备餐中": "PREPARING",     # 商家已接单，正在制作
    "配送中": "DELIVERING",    # 已交给骑手
    "已送达": "DELIVERED",     # 用户已签收
    "已取消": "CANCELLED",     # 订单已取消
    "退款中": "REFUNDING",     # 已发起退款，等待到账
    "已退款": "REFUNDED",      # 退款到账
}

# 合法状态迁移矩阵
VALID_TRANSITIONS = {
    "待接单": ["备餐中", "已取消"],
    "备餐中": ["配送中", "已取消"],
    "配送中": ["已送达"],       # 配送中不可取消
    "已送达": ["退款中"],       # 已送达只能走售后退款
    "已取消": [],               # 终态，不可再迁移
    "退款中": ["已退款"],
    "已退款": [],
}

def can_transition(current: str, target: str) -> bool:
    """检查状态迁移是否合法"""
    return target in VALID_TRANSITIONS.get(current, [])

def validate_cancel(status: str) -> tuple[bool, str]:
    """校验当前状态是否允许取消，返回 (是否允许, 原因)"""
    if status == "待接单":
        return True, ""
    elif status == "备餐中":
        return True, "商家已开始备餐，取消可能产生费用"
    elif status == "配送中":
        return False, "订单已在配送中，无法取消。如有问题请联系配送员。"
    elif status == "已送达":
        return False, "订单已送达，请申请售后处理。"
    elif status in ("已取消", "退款中", "已退款"):
        return False, f"订单当前状态为「{status}」，无需重复操作。"
    return True, ""