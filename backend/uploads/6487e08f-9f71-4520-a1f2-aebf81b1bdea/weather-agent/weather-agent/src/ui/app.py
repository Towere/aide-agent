"""Streamlit 天气穿搭助手主应用"""
import streamlit as st
import uuid
import sys
import os

# 添加上级目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入模块 - 使用 try-except 处理不同导入情况
try:
    from src.agent.react_agent import ReactAgent
except ImportError:
    # 备用导入方式
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../agent')))
    from react_agent import ReactAgent


# 页面配置
st.set_page_config(
    page_title="智能天气穿搭助手",
    page_icon="👔",
    layout="wide"
)

# 初始化 session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent" not in st.session_state:
    st.session_state.agent = ReactAgent()
if "last_chart" not in st.session_state:
    st.session_state.last_chart = None


st.title("🌤️ 智能天气穿搭助手")
st.markdown("输入城市名称，获取天气信息和穿搭建议！")


# 侧边栏
with st.sidebar:
    st.header("💡 使用提示")
    st.markdown("""
    - 直接输入城市名称，如：北京、上海、London
    - 查看天气和穿搭建议后，可以给出反馈
    - 反馈会帮助我更好地为你推荐
    """)

    st.divider()

    if st.button("🗑️ 清空对话", type="secondary"):
        st.session_state.agent.clear_session(st.session_state.session_id)
        st.session_state.messages = []
        st.session_state.last_chart = None
        st.rerun()


# 显示历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("chart") and os.path.exists(msg["chart"]):
            st.image(msg["chart"], caption="天气趋势图")


# 显示上一个图表
if st.session_state.last_chart and os.path.exists(st.session_state.last_chart):
    with st.container():
        st.image(st.session_state.last_chart, caption="天气趋势图")


# 反馈按钮（如果有穿搭建议）
if st.session_state.messages:
    last_msg = st.session_state.messages[-1]
    if last_msg["role"] == "assistant" and "穿" in last_msg["content"]:
        st.divider()
        st.markdown("**对穿搭建议有什么反馈？**")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🥵 穿多了", use_container_width=True, type="secondary"):
                with st.spinner("正在记录反馈..."):
                    response, _ = st.session_state.agent.chat("穿多了", st.session_state.session_id)
                    st.session_state.messages.append({"role": "user", "content": "穿多了"})
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()
        with col2:
            if st.button("👍 刚好", use_container_width=True, type="primary"):
                with st.spinner("正在记录反馈..."):
                    response, _ = st.session_state.agent.chat("刚好", st.session_state.session_id)
                    st.session_state.messages.append({"role": "user", "content": "刚好"})
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()
        with col3:
            if st.button("🥶 穿少了", use_container_width=True, type="secondary"):
                with st.spinner("正在记录反馈..."):
                    response, _ = st.session_state.agent.chat("穿少了", st.session_state.session_id)
                    st.session_state.messages.append({"role": "user", "content": "穿少了"})
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()


# 用户输入
if prompt := st.chat_input("输入城市名称，如：北京"):
    # 显示用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 调用 Agent
    with st.chat_message("assistant"):
        with st.spinner("正在思考..."):
            response, chart_path = st.session_state.agent.chat(prompt, st.session_state.session_id)
            st.markdown(response)

            if chart_path and os.path.exists(chart_path):
                st.image(chart_path, caption="天气趋势图")
                st.session_state.last_chart = chart_path
            else:
                st.session_state.last_chart = None

    # 保存助手消息
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "chart": chart_path
    })
