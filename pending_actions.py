# pending_actions.py
"""HITL：记录待用户确认的操作"""

_pending = {}  # {session_id: {"agent": ..., "action": ..., "params": ..., "summary": ...}}


def set_pending(session_id: str, agent: str, action: str, params: dict, summary: str):
    """记录一个待确认操作"""
    _pending[session_id] = {
        "agent": agent,
        "action": action,
        "params": params,
        "summary": summary,
    }


def get_pending(session_id: str):
    """获取待确认操作，没有返回 None"""
    return _pending.get(session_id)


def clear_pending(session_id: str):
    """清除待确认操作"""
    _pending.pop(session_id, None)


# 确认词 / 取消词（只在 pending 存在时使用）
_CONFIRM_WORDS = ["确认", "好的", "好哒", "可以", "是的", "行", "嗯",
                  "ok", "OK", "Ok", "yes", "Yes", "下单", "退吧", "退掉"]

_CANCEL_WORDS = ["取消", "不要", "不用", "算了", "别", "否",
                 "no", "No", "NO", "不下单", "不退"]


def is_confirmation(text: str) -> bool:
    """判断用户输入是否是确认"""
    text = text.strip()
    if len(text) > 10:  # 太长的不算简单确认
        return False
    if any(w in text for w in _CANCEL_WORDS):
        return False
    return any(w in text for w in _CONFIRM_WORDS)


def is_cancellation(text: str) -> bool:
    """判断用户输入是否是取消"""
    text = text.strip()
    if len(text) > 10:
        return False
    return any(w in text for w in _CANCEL_WORDS)