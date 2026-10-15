# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from graph_workflow import chat

app = FastAPI(title="一二布布外卖客服 API")


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        speaker, answer = chat(request.question)
        return ChatResponse(answer=f"【{speaker}】{answer}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {"message": "一二布布外卖客服系统运行中～"}