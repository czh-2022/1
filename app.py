import streamlit as st
import requests
import json
import uuid

# 后端 API 地址
API_URL = "http://localhost:8002"

st.set_page_config(page_title="智能养老营养师", page_icon="🥗", layout="wide")

st.title("🥗 智能养老营养师对话系统")
st.markdown("为您提供专业的个性化膳食建议与慢病管理指导")
st.markdown("💡 **提示**: 您可以直接描述您的症状或问题，无需填写复杂的表格。例如：*“我有糖尿病，最近总是口渴，该吃什么？”*")

# 初始化会话状态 (Session State)
if "profile_id" not in st.session_state:
    st.session_state.profile_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "nutrition_targets" not in st.session_state:
    st.session_state.nutrition_targets = None

# 自动初始化访客画像 (如果不存在)
if not st.session_state.profile_id:
    # 默认访客配置
    guest_profile = {
        "age": 65,
        "gender": "male", 
        "height_cm": 165.0,
        "weight_kg": 60.0,
        "activity_level": "light",
        "health_conditions": [], # 空的健康状况，将由 LLM 意图识别自动检测
        "allergies": [],
        "preferences": "通用"
    }
    
    try:
        with st.spinner("正在初始化智能助手..."):
            response = requests.post(f"{API_URL}/profile", json=guest_profile)
            if response.status_code == 200:
                data = response.json()
                st.session_state.profile_id = data["profile_id"]
                st.session_state.nutrition_targets = data["nutrition_targets"]
            else:
                st.error(f"系统初始化失败: {response.text}")
    except Exception as e:
        st.error(f"连接服务器失败: {e}")


import streamlit.components.v1 as components

# 聊天界面 (Chat Interface)
if st.session_state.profile_id:
    # 注入自动关闭脚本
    # 当浏览器窗口关闭或刷新时，发送请求给后端以关闭服务
    components.html(
        f"""
        <script>
            window.addEventListener('beforeunload', function (e) {{
                // 使用 navigator.sendBeacon 发送关闭信号，确保在页面卸载时能发出请求
                navigator.sendBeacon("{API_URL}/system/shutdown");
            }});
        </script>
        """,
        height=0,
        width=0,
    )

    # 显示历史消息
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 聊天输入框
    if prompt := st.chat_input("请输入您的问题 (例如：高血压早餐吃什么好？)"):
        # 添加用户消息到状态
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # 调用 API
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("思考中...")
            
            try:
                payload = {
                    "message": prompt,
                    "history": st.session_state.messages[:-1] # 发送不包含当前消息的历史记录，避免后端重复
                }
                
                response = requests.post(f"{API_URL}/chat/{st.session_state.profile_id}", json=payload)
                
                if response.status_code == 200:
                    reply = response.json()["reply"]
                    message_placeholder.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                else:
                    message_placeholder.markdown(f"Error: {response.text}")
            except Exception as e:
                message_placeholder.markdown(f"Connection Error: {e}")

else:
    st.warning("正在连接后端服务，请确保后端已启动...")
