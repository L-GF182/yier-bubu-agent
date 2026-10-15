# graph_workflow.py
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage
from agents.supervisor import route_supervisor
from agents.yier_agent import yier_respond
from agents.bubu_agent import bubu_respond


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    next_agent: str
    session_id: str


def supervisor_node(state: AgentState):
    last_msg = state["messages"][-1].content
    session_id = state.get("session_id", "default")
    next_agent = route_supervisor(last_msg, session_id)
    return {"next_agent": next_agent}


def yier_node(state: AgentState):
    last_msg = state["messages"][-1].content
    session_id = state.get("session_id", "default")
    answer = yier_respond(last_msg, session_id)
    return {"messages": [AIMessage(content=answer)]}


def bubu_node(state: AgentState):
    last_msg = state["messages"][-1].content
    session_id = state.get("session_id", "default")
    answer = bubu_respond(last_msg, session_id)
    return {"messages": [AIMessage(content=answer)]}


def route_after_supervisor(state: AgentState):
    return state.get("next_agent", "yier")


graph = StateGraph(AgentState)
graph.add_node("supervisor", supervisor_node)
graph.add_node("yier", yier_node)
graph.add_node("bubu", bubu_node)

graph.add_edge(START, "supervisor")
graph.add_conditional_edges(
    "supervisor",
    route_after_supervisor,
    {"yier": "yier", "bubu": "bubu"}
)
graph.add_edge("yier", END)
graph.add_edge("bubu", END)

app = graph.compile()


def chat(question: str, session_id: str = "default"):
    """返回 (speaker, answer) 元组，speaker 为 '一二' 或 '布布'"""
    result = app.invoke({
        "messages": [HumanMessage(content=question)],
        "next_agent": "",
        "session_id": session_id,
    })
    next_agent = result.get("next_agent", "yier")
    speaker = "一二" if next_agent == "yier" else "布布"
    answer = result["messages"][-1].content
    return speaker, answer