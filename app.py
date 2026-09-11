import streamlit as st
import json
import random
from dotenv import load_dotenv
import os

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.tools import tool

# 加载环境变量
load_dotenv()

# ============ 页面配置 ============
st.set_page_config(page_title="🔮 AI塔罗占卜师", page_icon="🔮", layout="centered")
st.title("🔮 AI塔罗占卜师")
st.caption("让AI为你解读命运的神秘之牌")

# ============ 加载塔罗牌数据 ============
def load_cards():
    with open("tarot_cards.json", "r", encoding="utf-8") as f:
        return json.load(f)

cards = load_cards()

# ============ 定义抽牌工具 ============
@tool
def draw_cards(query: str) -> str:
    """抽取塔罗牌。用户说'抽牌'或'占卜'时调用。
    参数 query 可以包含数量提示，如 '抽3张'、'抽五张'，默认抽1张。
    """
    if "3" in query or "三" in query:
        num = 3
    elif "5" in query or "五" in query:
        num = 5
    else:
        num = 1

    num = min(num, len(cards))
    drawn = random.sample(cards, num)

    result = f"✨ 为你抽了 {num} 张牌：\n\n"
    for card in drawn:
        # 随机决定正位或逆位（各50%概率）
        is_upright = random.choice([True, False])
        position = "正位" if is_upright else "逆位"
        meaning = card['meaning_positive'] if is_upright else card['meaning_negative']

        result += f"🃏 {card['name']}（{position}）\n"
        result += f"   牌义：{meaning}\n\n"

    return result


# ============ 创建 Agent ============
def build_agent():
    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        temperature=0.8,
    )

    system_prompt = (
        "你是一位神秘的AI塔罗占卜师，拥有千年智慧。你的风格温柔、富有哲理，善于引导用户思考。\n"
        "当用户想要占卜、抽牌、询问运势时，你必须调用 draw_cards 工具来抽牌，"
        "然后结合抽到的牌义和用户的问题，给出温暖、有深度、有针对性的解读。\n"
        "如果用户只是在打招呼或闲聊，就友好地回应，并引导用户提出想占卜的问题。"
    )

    # 使用新版 create_agent
    agent = create_agent(
        model=llm,
        tools=[draw_cards],
        system_prompt=system_prompt,
    )

    return agent


# ============ 初始化会话状态 ============
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent" not in st.session_state:
    st.session_state.agent = build_agent()

# ============ 显示历史消息 ============
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ============ 用户输入 ============
if user_input := st.chat_input("告诉我你的困扰，让我为你抽牌指引..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("🔮 命运之轮在转动..."):
            try:
                # 新版 create_agent 返回的对象直接用 invoke
                response = st.session_state.agent.invoke(
                    {"messages": [{"role": "user", "content": user_input}]}
                )
                # 新版的输出格式不同，需要从 messages 里提取最后一条
                messages = response.get("messages", [])
                answer = messages[-1].content if messages else "命运暂时无法解读，请再试一次..."
            except Exception as e:
                answer = f"🙏 占卜师暂时无法连接命运之轮，请稍后再试。\n\n错误：{e}"

            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})