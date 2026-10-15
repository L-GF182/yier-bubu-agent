# agents/supervisor.py
import json
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from config import SUPERVISOR_PROMPT
from pending_actions import get_pending, is_confirmation, is_cancellation, clear_pending

load_dotenv()

llm = ChatOpenAI(
    temperature=0,
    model="qwen3.8-flash",
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    openai_api_base=os.getenv("OPENAI_BASE_URL"),
)


def route_supervisor(question: str, session_id: str = "default") -> str:
    """根据用户问题，返回下一个应该处理的 Agent：yier / bubu"""

    # ========== 0. 优先处理待确认操作（HITL） ==========
    pending = get_pending(session_id)
    if pending:
        if is_confirmation(question) or is_cancellation(question):
            print(f"🔀 检测到待确认操作，路由到 {pending['agent']}：{question}")
            return pending["agent"]
        else:
            print(f"🔀 用户改变了意图，清除待确认操作")
            clear_pending(session_id)

    # ========== 1. 完全交给 LLM 判断 ==========
    try:
        response = llm.invoke([
            SystemMessage(content=SUPERVISOR_PROMPT),
            HumanMessage(content=question),
        ])
        text = response.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()

        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            text = text[start:end]

        data = json.loads(text)
        next_agent = data.get("next_agent", "yier")

        if next_agent == "direct":
            next_agent = "yier"

        print(f"🔀 LLM 路由到 {next_agent}：{question}")
        return next_agent
    except Exception as e:
        print(f"⚠️ Supervisor 解析失败，默认转交一二：{e}")
        return "yier"