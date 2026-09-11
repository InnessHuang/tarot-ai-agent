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
    参数 query 可以包含数量提示，如 '抽7张'、'抽十张'，默认抽1张。
    如果用户没有指定数量，由 Agent 根据问题复杂程度决定抽几张：
    - 简单问题（今日运势、单张指引）→ 抽1张
    - 复杂问题（感情、事业、选择）→ 抽3张
    """
    # 中文数字映射
    cn_num = {
        "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
        "六": 6, "七": 7, "八": 8, "九": 9, "十": 10
    }

    num = None

    # 先尝试从 query 里提取阿拉伯数字（如 "抽7张"）
    import re
    match = re.search(r'(\d+)', query)
    if match:
        num = int(match.group(1))

    # 如果没有阿拉伯数字，尝试提取中文数字（如 "抽七张"）
    if num is None:
        for cn, val in cn_num.items():
            if cn in query:
                num = val
                break

    # 如果还是没指定，默认抽1张（Agent 会在 system_prompt 里被要求根据问题复杂度决定）
    if num is None:
        num = 1

    # 限制范围：最少1张，最多不超过牌库总数
    num = max(1, min(num, len(cards)))

    drawn = random.sample(cards, num)

    result = f"✨ 为你抽了 {num} 张牌：\n\n"
    for card in drawn:
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
        "你是一位神秘的AI塔罗占卜师，拥有千年智慧。你的风格温柔、富有哲理，善于引导用户思考。\n\n"
        "【抽牌规则】\n"
        "当用户想要占卜、抽牌、询问运势时，你必须调用 draw_cards 工具来抽牌。\n"
        "关于抽牌数量，按以下规则判断：\n"
        "1. 如果用户明确说了数量（如'抽5张''抽七张'），就按用户说的数量调用工具。\n"
        "2. 如果用户没有指定数量：\n"
        "   - 简单问题（今日运势、单张指引、简单是非题）→ 抽1张\n"
        "   - 复杂问题（感情关系、职业选择、人生方向、需要多角度分析）→ 抽3张\n"
        "3. 调用工具时，在参数里明确写出数量，比如 '抽1张' 或 '抽3张'。\n\n"
        "【解读规则】\n"
        "抽到牌后，结合每张牌的牌义和位置（正位/逆位），给出温暖、有深度、有针对性的解读。\n"
        "严格依据抽牌结果中的'正位'或'逆位'来解读，不要自行猜测或混淆。\n\n"
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