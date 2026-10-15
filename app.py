# app.py
import os
import gradio as gr
from graph_workflow import chat
import base64

def img_to_base64(path):
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

# ========== 聊天框头像（保持不变） ==========
YIER_AVATAR = "assets/yierbubu.png"
USER_AVATAR = "assets/user.png"

# ========== 标题专用图片 ==========
TITLE_YIER = "assets/yier.png"
TITLE_BUBU = "assets/bubu.png"

if not os.path.exists(YIER_AVATAR):
    YIER_AVATAR = None
if not os.path.exists(USER_AVATAR):
    USER_AVATAR = None
def chat_fn(message, history):
    """Gradio 聊天回调"""
    try:
        speaker, response = chat(message, session_id="default")
        return f"【{speaker}】{response}"
    except Exception as e:
        return f"抱歉，出错了：{str(e)}"


# ========== 自定义粉色主题 CSS ==========
CUSTOM_CSS = """
html, body, .gradio-container {
    background: linear-gradient(180deg, #fff0f5 0%, #ffe4ec 100%) !important;
    min-height: 100vh !important;
}

.gradio-container {
    max-width: 100% !important;
    padding: 20px 40px !important;
}

/* 标题：字号适中 */
#title-md {
    text-align: center !important;
    padding: 16px 0 4px 0 !important;
}
#title-md h1 {
    text-align: center !important;
    color: #d63384 !important;
    font-size: 2em !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    margin: 0 !important;
}
#subtitle-md {
    text-align: center !important;
    padding: 0 0 16px 0 !important;
}
#subtitle-md p {
    text-align: center !important;
    color: #a64265 !important;
    font-size: 1em !important;
    margin: 0 !important;
}

#my-chatbot {
    background: #ffffff !important;
    border: 1px solid #ffd6e2 !important;
    border-radius: 16px !important;
    padding: 8px !important;
    box-shadow: 0 2px 12px rgba(214, 51, 132, 0.06) !important;
}

/* 输入框 */
textarea, input[type="text"] {
    border-radius: 12px !important;
    border: 1.5px solid #ffd6e2 !important;
    background: #ffffff !important;
    min-height: 44px !important;
    font-size: 15px !important;
}
textarea:focus, input[type="text"]:focus {
    border-color: #ff6fa5 !important;
    box-shadow: 0 0 0 3px rgba(255, 111, 165, 0.12) !important;
}

/* 发送按钮 */
#send-btn, #send-btn button {
    background: linear-gradient(135deg, #ff8ab8 0%, #d63384 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    font-size: 1.4em !important;
    font-weight: 700 !important;
    height: 44px !important;
    min-height: 44px !important;
    max-height: 44px !important;
    width: 60px !important;
    min-width: 60px !important;
    max-width: 60px !important;
    padding: 0 !important;
    box-shadow: 0 2px 8px rgba(214, 51, 132, 0.2) !important;
    transition: transform 0.15s !important;
}
#send-btn:hover, #send-btn button:hover {
    transform: scale(1.05) !important;
    box-shadow: 0 4px 12px rgba(214, 51, 132, 0.35) !important;
}

/* 清空按钮 */
#clear-btn, #clear-btn button {
    background: #ffe4ec !important;
    color: #d63384 !important;
    border: 1.5px solid #ffd6e2 !important;
    border-radius: 12px !important;
    height: 44px !important;
    min-height: 44px !important;
    max-height: 44px !important;
    padding: 0 16px !important;
    font-size: 16px !important;
    font-weight: 600 !important;
}

/* 头像放大 */
#my-chatbot img.avatar-image,
#my-chatbot .avatar-image {
    width: 72px !important;
    height: 72px !important;
    min-width: 72px !important;
    min-height: 72px !important;
    max-width: 72px !important;
    max-height: 72px !important;
    border-radius: 50% !important;
    object-fit: contain !important;
    background-color: #ffffff !important;
}

#my-chatbot .avatar-container {
    width: 72px !important;
    height: 72px !important;
    min-width: 72px !important;
    min-height: 72px !important;
    max-width: 72px !important;
    max-height: 72px !important;
    flex: 0 0 72px !important;
    border-radius: 50% !important;
    overflow: hidden !important;
    background-color: #ffffff !important;
}

/* 全局字体：微软雅黑 */
html, body, .gradio-container,
#my-chatbot,
#my-chatbot *,
.gradio-container textarea,
.gradio-container input,
.gradio-container button,
#title-md h1,
#subtitle-md p {
    font-family: "Microsoft YaHei", "微软雅黑", "PingFang SC", "Helvetica Neue", Arial, sans-serif !important;
}

/* 消息字体放大 */
#my-chatbot .message,
#my-chatbot .message p,
#my-chatbot .message span,
#my-chatbot .message div {
    font-size: 17px !important;
    line-height: 1.7 !important;
}

/* 输入框字体放大 */
#my-chatbot textarea,
.gradio-container textarea,
.gradio-container input[type="text"] {
    font-size: 17px !important;
}

::-webkit-scrollbar-thumb {
    background: #ffd6e2 !important;
    border-radius: 8px !important;
}

/* 快捷按钮 */
#quick-menu-btn, #quick-order-btn, #quick-query-btn, #quick-advance-btn {
    background: #ffffff !important;
    color: #d63384 !important;
    border: 1.5px solid #ffd6e2 !important;
    border-radius: 20px !important;
    font-size: 14px !important;
    height: 36px !important;
    min-height: 36px !important;
    padding: 0 16px !important;
}
#quick-menu-btn:hover, #quick-order-btn:hover, #quick-query-btn:hover, #quick-advance-btn:hover {
    background: #ffe4ec !important;
    border-color: #ff6fa5 !important;
}
"""


# ========== 构建界面 ==========
with gr.Blocks(title="一二布布外卖客服") as demo:
    _yier_b64 = img_to_base64(TITLE_YIER)
    _bubu_b64 = img_to_base64(TITLE_BUBU)

    gr.Markdown(
        f'<h1 style="text-align:center; color:#d63384; font-size:2em; '
        f'font-weight:700; letter-spacing:1px; margin:0; '
        f'display:flex; align-items:center; justify-content:center; gap:0px;">'
        f'<img src="data:image/png;base64,{_yier_b64}" '
        f'style="height:52px; width:52px; border-radius:12px; object-fit:contain; background:#fff0f5; margin-right:-8px;">'
        f'<img src="data:image/png;base64,{_bubu_b64}" '
        f'style="height:52px; width:52px; border-radius:12px; object-fit:contain; background:#fff0f5;">'
        f'一二布布外卖客服'
        f'</h1>',
        elem_id="title-md",
    )
    gr.Markdown(
        "一二和布布随时为你服务～",
        elem_id="subtitle-md",
    )

    chatbot = gr.Chatbot(
        avatar_images=(USER_AVATAR, YIER_AVATAR),
        height=720,
        show_label=False,
        elem_id="my-chatbot",
        elem_classes=["chatbot"],
    )
    # app.py 中 chatbot 定义之后、with gr.Row() 之前插入：

    with gr.Row():
        menu_btn = gr.Button("📋 查看菜单", size="sm", elem_id="quick-menu-btn")
        order_hint_btn = gr.Button("🛒 我要点餐", size="sm", elem_id="quick-order-btn")
        query_hint_btn = gr.Button("🔍 查订单", size="sm", elem_id="quick-query-btn")
        advance_btn = gr.Button("⏩ 模拟商家推进", size="sm", elem_id="quick-advance-btn")

    def quick_menu(chat_history):
        from tools.order_tools import get_menu
        menu = get_menu.invoke({"category": ""})
        chat_history.append({"role": "user", "content": "看看菜单"})
        chat_history.append({"role": "assistant", "content": f"【一二】一二来给你看看菜单～\n\n{menu}"})
        return chat_history


    def quick_order(chat_history):
        chat_history.append({"role": "user", "content": "我要点餐"})
        chat_history.append(
            {"role": "assistant", "content": "【一二】好哒～你想吃什么呀？可以告诉一二商品ID和数量，比如「M001 1份」～"})
        return chat_history


    def quick_query(chat_history):
        chat_history.append({"role": "user", "content": "查订单"})
        chat_history.append(
            {"role": "assistant", "content": "【一二】请把你的订单号告诉一二，比如 ORD-20261012-XXXX，一二帮你查～"})
        return chat_history

    def quick_advance(chat_history):
        """自动找最新一个未完成的订单，推进它的状态"""
        from database import get_db
        from tools.order_tools import advance_order_status

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT order_id FROM orders "
            "WHERE status IN ('待接单', '备餐中', '配送中') "
            "ORDER BY created_at DESC LIMIT 1"
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            chat_history.append({"role": "user", "content": "模拟商家推进"})
            chat_history.append({
                "role": "assistant",
                "content": "【系统】当前没有可推进的订单。请先下一单，或订单都已送达/取消。"
            })
            return chat_history

        order_id = row["order_id"]
        result = advance_order_status.invoke({"order_id": order_id})
        chat_history.append({"role": "user", "content": f"模拟商家推进 {order_id}"})
        chat_history.append({"role": "assistant", "content": f"【系统】\n{result}"})
        return chat_history


    menu_btn.click(quick_menu, [chatbot], [chatbot])
    order_hint_btn.click(quick_order, [chatbot], [chatbot])
    query_hint_btn.click(quick_query, [chatbot], [chatbot])
    advance_btn.click(quick_advance, [chatbot], [chatbot])

    with gr.Row():
        msg = gr.Textbox(
            placeholder="输入你的问题...",
            container=False,
            scale=6,
            lines=1,
        )
        submit_btn = gr.Button("➤", variant="primary", elem_id="send-btn", scale=0)
        clear_btn = gr.Button("清空对话", variant="secondary", elem_id="clear-btn", scale=0)

    def respond(message, chat_history):
        if not message.strip():
            yield "", chat_history
            return
        chat_history.append({"role": "user", "content": message})
        chat_history.append({"role": "assistant", "content": ""})
        yield "", chat_history
        response = chat_fn(message, chat_history)
        chat_history[-1] = {"role": "assistant", "content": response}
        yield "", chat_history

    msg.submit(respond, [msg, chatbot], [msg, chatbot])
    submit_btn.click(respond, [msg, chatbot], [msg, chatbot])
    clear_btn.click(lambda: None, None, chatbot, queue=False)


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        theme=gr.themes.Soft(),
        css=CUSTOM_CSS,
        show_error=True,
    )