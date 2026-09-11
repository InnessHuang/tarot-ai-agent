import streamlit as st
import json
import random
from dotenv import load_dotenv
import os
import base64
from pathlib import Path
import re

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.tools import tool

load_dotenv()

_DRAWN_FILE = Path("_last_drawn.json")

st.set_page_config(page_title="🔮 AI塔罗占卜师", page_icon="🔮", layout="centered")

BG_PATH = Path("assets/backgrounds/bg1.jpg")

def img_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

bg_base64 = img_to_base64(BG_PATH)

st.markdown(f"""
<style>
    .stApp {{
        background-image: url("data:image/jpeg;base64,{bg_base64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    h1 {{
        color: #1a1a2e !important;
        text-shadow: -1px -1px 0 white, 1px -1px 0 white, -1px 1px 0 white, 1px 1px 0 white, 0 0 10px rgba(255,255,255,0.8);
    }}
    .stChatMessage {{
        background: rgba(200, 225, 255, 0.85) !important;
        border-radius: 12px;
        padding: 10px;
    }}
    .stChatInput button {{
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #60a5fa 100%) !important;
        color: white !important;
        box-shadow: 0 0 10px rgba(96, 165, 250, 0.5) !important;
    }}
    .stChatInput button:hover {{
        background: linear-gradient(135deg, #1e40af 0%, #2563eb 50%, #3b82f6 100%) !important;
        box-shadow: 0 0 16px rgba(96, 165, 250, 0.8) !important;
    }}
    .st-key-card_float_container {{
        position: fixed !important;
        right: 30px !important;
        top: 120px !important;
        z-index: 99999 !important;
        width: auto !important;
        background: transparent !important;
    }}
    .card-float {{
        display: flex !important;
        flex-direction: row !important;
        gap: 12px !important;
        background: rgba(255, 255, 255, 0.15) !important;
        padding: 12px !important;
        border-radius: 12px !important;
    }}
    .card-float img {{
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        display: block;
    }}
    .card-float .card-label {{
        text-align: center;
        color: white;
        font-size: 12px;
        margin-top: 4px;
        text-shadow: 0 0 4px rgba(0,0,0,0.9);
    }}
    .stMarkdown, .element-container {{
        transform: none !important;
    }}
</style>
""", unsafe_allow_html=True)

st.title("AI塔罗占卜师")
st.markdown(
    '<p style="color: #1a1a2e; font-weight: 700; font-size: 1.2rem; text-align: left; margin-left: 0%; white-space: nowrap; text-shadow: -0.5px -0.5px 0 white, 0.5px -0.5px 0 white, -0.5px 0.5px 0 white, 0.5px 0.5px 0 white;">让AI为你解读命运的神秘之牌</p>',
    unsafe_allow_html=True
)


def load_cards():
    with open("tarot_cards.json", "r", encoding="utf-8") as f:
        return json.load(f)

cards = load_cards()


@tool
def draw_cards(query: str) -> str:
    """抽取塔罗牌。用户说'抽牌'或'占卜'时调用。
    参数 query 可以包含数量提示，如 '抽7张'、'抽十张'，默认抽1张。
    """
    cn_num = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
              "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}

    num = None
    match = re.search(r'(\d+)', query)
    if match:
        num = int(match.group(1))

    if num is None:
        for cn, val in cn_num.items():
            if cn in query:
                num = val
                break

    if num is None:
        num = 1

    num = max(1, min(num, len(cards)))
    drawn = random.sample(cards, num)

    drawn_info = []
    result = f"✨ 为你抽了 {num} 张牌：\n\n"
    for card in drawn:
        is_upright = random.choice([True, False])
        position = "正位" if is_upright else "逆位"
        meaning = card['meaning_positive'] if is_upright else card['meaning_negative']
        result += f"🃏 {card['name']}（{position}）\n   牌义：{meaning}\n\n"
        drawn_info.append({"id": card["id"], "name": card["name"], "position": position})

    with open(_DRAWN_FILE, "w", encoding="utf-8") as f:
        json.dump(drawn_info, f, ensure_ascii=False)
    return result


def build_agent():
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        temperature=0.8,
    )
    system_prompt = (
        "你是一位神秘的AI塔罗占卜师，拥有千年智慧。你的风格温柔、富有哲理，善于引导用户思考。\n\n"
        "【抽牌规则】\n"
        "当用户想要占卜、抽牌、询问运势时，你必须调用 draw_cards 工具来抽牌。\n"
        "关于抽牌数量，按以下规则判断：\n"
        "1. 如果用户明确说了数量（如'抽5张''抽七张'），就按用户说的数量调用工具。\n"
        "2. 如果用户没有指定数量：简单问题→抽1张；复杂问题→抽3张。\n"
        "3. 调用工具时，在参数里明确写出数量，比如 '抽1张' 或 '抽3张'。\n\n"
        "【解读规则】\n"
        "抽到牌后，结合每张牌的牌义和位置（正位/逆位），给出温暖、有深度、有针对性的解读。\n"
        "严格依据抽牌结果中的'正位'或'逆位'来解读。\n\n"
        "如果用户只是在打招呼或闲聊，就友好地回应，并引导用户提出想占卜的问题。"
    )
    agent = create_agent(model=llm, tools=[draw_cards], system_prompt=system_prompt)
    return agent


if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent" not in st.session_state:
    st.session_state.agent = build_agent()
if "current_cards" not in st.session_state:
    st.session_state.current_cards = []


def render_floating_cards(card_list):
    if not card_list:
        return
    n = len(card_list)
    if n == 1:
        width = 150
    elif n == 3:
        width = 100
    else:
        width = 80

    cards_html = ""
    for card in card_list:
        img_path = Path("assets/cards") / f"{card['id']}.jpg"
        if img_path.exists():
            img_b64 = img_to_base64(img_path)
            img_tag = f'<img src="data:image/jpeg;base64,{img_b64}" width="{width}">'
        else:
            img_tag = f'<div style="width:{width}px;height:{int(width*1.7)}px;background:#333;color:white;display:flex;align-items:center;justify-content:center;">🃏</div>'
        cards_html += f'<div>{img_tag}<div class="card-label">{card["name"]}<br>（{card["position"]}）</div></div>'

    st.markdown(f'<div class="card-float">{cards_html}</div>', unsafe_allow_html=True)


# ============ 1. 显示历史消息 ============
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🎩"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])


# ============ 2. 处理用户输入 ============
if user_input := st.chat_input("告诉我你的困扰，让我为你抽牌指引..."):
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    if _DRAWN_FILE.exists():
        _DRAWN_FILE.unlink()

    with st.chat_message("assistant", avatar="🎩"):
        with st.spinner("命运之轮在转动..."):
            try:
                response = st.session_state.agent.invoke(
                    {"messages": [{"role": "user", "content": user_input}]}
                )
                messages = response.get("messages", [])
                answer = messages[-1].content if messages else "命运暂时无法解读，请再试一次..."
            except Exception as e:
                answer = f"🙏 占卜师暂时无法连接命运之轮，请稍后再试。\n\n错误：{e}"

            drawn_cards = []
            if _DRAWN_FILE.exists():
                try:
                    with open(_DRAWN_FILE, "r", encoding="utf-8") as f:
                        drawn_cards = json.load(f)
                    _DRAWN_FILE.unlink()
                except Exception:
                    drawn_cards = []

            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

            if drawn_cards:
                st.session_state.current_cards = drawn_cards
                # 不调 st.rerun()，牌面在下面的固定容器里重新渲染


# ============ 3. 渲染右侧固定牌面（每次都执行，只创建一次） ============
if st.session_state.current_cards:
    with st.container(key="card_float_container"):
        render_floating_cards(st.session_state.current_cards)