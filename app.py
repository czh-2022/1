import streamlit as st
import requests
import json

# Backend URL
API_URL = "http://localhost:8002"

st.set_page_config(page_title="智能养老营养师", page_icon="🥗", layout="wide")

st.title("🥗 智能养老营养师对话系统")
st.markdown("为您提供专业的个性化膳食建议与慢病管理指导")

# Initialize session state
if "profile_id" not in st.session_state:
    st.session_state.profile_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "nutrition_targets" not in st.session_state:
    st.session_state.nutrition_targets = None

# Sidebar for Profile Settings
with st.sidebar:
    st.header("👤 用户画像设置")
    
    with st.form("profile_form"):
        age = st.number_input("年龄", min_value=50, max_value=120, value=65)
        gender = st.selectbox("性别", ["male", "female"], format_func=lambda x: "男" if x == "male" else "女")
        height = st.number_input("身高 (cm)", min_value=100.0, max_value=250.0, value=165.0)
        weight = st.number_input("体重 (kg)", min_value=30.0, max_value=200.0, value=60.0)
        activity = st.selectbox("活动水平", 
            ["sedentary", "light", "moderate", "active", "very_active"],
            format_func=lambda x: {
                "sedentary": "久坐/卧床", 
                "light": "轻体力 (如散步)", 
                "moderate": "中体力 (如家务)", 
                "active": "重体力", 
                "very_active": "极重体力"
            }[x]
        )
        
        conditions = st.multiselect("慢性病史", 
            ["hypertension", "diabetes", "kidney_disease", "gout", "heart_disease"],
            format_func=lambda x: {
                "hypertension": "高血压", 
                "diabetes": "糖尿病", 
                "kidney_disease": "肾病", 
                "gout": "痛风", 
                "heart_disease": "心脏病"
            }[x]
        )
        
        allergies = st.text_input("过敏食物 (逗号分隔)", value="")
        preferences = st.text_area("饮食偏好 (如忌口、口味)", value="清淡口味")
        
        submit_btn = st.form_submit_button("生成/更新画像")
        
        if submit_btn:
            profile_data = {
                "age": int(age),
                "gender": gender,
                "height_cm": height,
                "weight_kg": weight,
                "activity_level": activity,
                "health_conditions": conditions,
                "allergies": [x.strip() for x in allergies.split(",") if x.strip()],
                "preferences": preferences
            }
            
            try:
                response = requests.post(f"{API_URL}/profile", json=profile_data)
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.profile_id = data["profile_id"]
                    st.session_state.nutrition_targets = data["nutrition_targets"]
                    st.success("画像已更新！")
                else:
                    st.error(f"更新失败: {response.text}")
            except Exception as e:
                st.error(f"连接服务器失败: {e}")

# Display Nutrition Targets if available
if st.session_state.nutrition_targets:
    targets = st.session_state.nutrition_targets
    st.info(f"""
    **每日营养目标参考**:
    🔥 热量: {targets['calories']} kcal | 🥩 蛋白质: {targets['protein_g']}g | 🥑 脂肪: {targets['fat_g']}g | 🍞 碳水: {targets['carbs_g']}g
    🧂 钠限制: {targets['sodium_mg']}mg
    """)

# Chat Interface
if st.session_state.profile_id:
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("请输入您的问题 (例如：高血压早餐吃什么好？)"):
        # Add user message to state
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Call API
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("思考中...")
            
            try:
                payload = {
                    "message": prompt,
                    "history": st.session_state.messages[:-1] # Send history excluding current message to avoid duplication if backend handles it
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
    st.warning("请先在左侧侧边栏设置个人画像以开始对话。")
