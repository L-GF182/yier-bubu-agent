# agents/bubu_agent.py
import os
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config import BUBU_PROMPT
from tools.order_tools import process_refund,check_order_status
from pending_actions import set_pending, get_pending, clear_pending, is_confirmation, is_cancellation

load_dotenv()

llm = ChatOpenAI(
    temperature=0.1,
    model="qwen3.8-flash",
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    openai_api_base=os.getenv("OPENAI_BASE_URL"),
)

def bubu_respond(question: str, session_id: str = "default") -> str:
    """布布回复：处理退单/退款（带 HITL 确认）"""

    # ========== 0. 检查待确认操作（HITL） ==========
    pending = get_pending(session_id)
    if pending and pending["agent"] == "bubu":
        if is_confirmation(question):
            clear_pending(session_id)
            result = process_refund.invoke(pending["params"])
            return f"布布收到，我来处理。\n\n{result}"
        elif is_cancellation(question):
            clear_pending(session_id)
            return "好的，布布已取消这次退单操作。还有其他需要吗？"
        else:
            clear_pending(session_id)

    # ========== 1. 退单/查单意图 ==========
    match = re.search(r"ORD-[\dA-Z-]+", question)
    if match:
        order_id = match.group()
        if "退" in question or "取消" in question:
            # 先查订单详情，用于展示给用户确认
            detail = check_order_status.invoke({"order_id": order_id})

            # 不直接退单，先记录 pending，返回带明细的确认提示
            set_pending(
                session_id=session_id,
                agent="bubu",
                action="process_refund",
                params={"order_id": order_id, "reason": "用户主动申请"},
                summary=f"订单 {order_id}",
            )
            return (
                f"布布收到～你要退的是：\n\n"
                f"{detail}\n\n"
                f"确认要退吗？回复「确认」布布就帮你处理～"
            )
        else:
            result = check_order_status.invoke({"order_id": order_id})
            return f"布布帮你查了一下。\n{result}"

    # ========== 2. 兜底：交给 LLM ==========
    response = llm.invoke([
        SystemMessage(content=BUBU_PROMPT),
        HumanMessage(content=question),
    ])
    return response.content