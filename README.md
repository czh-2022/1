# 智能养老营养师对话系统 (Smart Elderly Nutritionist)

基于大语言模型（LLM）的老年人个性化营养健康助手。

## 🌟 核心功能

1. **个性化画像建立**：采集年龄、身高体重、活动水平、慢性病史（高血压/糖尿病/肾病等）、过敏与偏好。
2. **智能营养计算**：基于 Mifflin-St Jeor 公式与活动系数，结合慢病规则自动生成每日热量、宏量营养素及钠盐限额。
3. **AI 对话咨询**：
   - 回答饮食宜忌（如“痛风能吃豆腐吗？”）。
   - 生成一日食谱建议。
   - 识别高风险请求并触发安全护栏。
4. **安全与合规**：内置医学免责声明，针对急症建议就医，不提供处方。

## 🛠️ 技术栈

- **后端**: Python FastAPI
- **AI**: OpenAI API (兼容 DeepSeek/Azure/LocalLLM) + Prompt Engineering
- **前端**: Streamlit (Web UI)
- **数据**: 内存存储 (MVP阶段) + Pydantic 校验

## 🚀 快速开始

### 1. 环境准备

确保已安装 Python 3.8+。

```bash
# 进入项目目录
cd smart_elderly_nutritionist

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 (可选)

如果需要使用真实 LLM 能力，请配置 `.env` 文件：

1. 复制 `.env.example` 为 `.env`
2. 填入你的 API Key (OpenAI 或 兼容服务)

```bash
copy .env.example .env
```

**注意**: 如果不配置 API Key，系统将自动运行在 **Mock 模式**，仅返回预设的固定回复，用于演示流程。

### 3. 运行系统

双击运行 `run_app.bat` 脚本（Windows），或手动运行：

**终端 1 (后端)**:
```bash
py -m uvicorn main:app --reload
```

**终端 2 (前端)**:
```bash
py -m streamlit run app.py
```

访问前端页面：`http://localhost:8501`

### 4. 触发知识库同步 (PowerShell)

在 PowerShell 中，直接使用 `curl` 可能会遇到问题（因为它是 `Invoke-WebRequest` 的别名）。请使用以下命令：

```powershell
# 推荐使用我们提供的测试脚本
.\test_api.ps1

# 或者手动执行
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/knowledge/trigger_sync"
```

## 🧪 测试用例

1. **高血压用户**:
   - 画像：65岁，高血压，轻体力活动。
   - 提问：“我早餐吃咸菜喝粥行吗？”
   - 预期：AI 建议减少咸菜（高钠），推荐燕麦牛奶或杂粮粥，并提醒每日盐摄入量。

2. **糖尿病用户**:
   - 画像：70岁，糖尿病，久坐。
   - 提问：“我想吃西瓜。”
   - 预期：AI 建议限量（如200g以内），两餐之间吃，监测血糖。

## 📁 目录结构

- `main.py`: 后端 API 入口
- `app.py`: 前端 Streamlit 应用
- `llm_service.py`: LLM 调用封装与 Mock 逻辑
- `prompts.py`: 系统提示词与安全规则
- `utils.py`: 营养学计算公式
- `models.py`: 数据模型定义

---
*Disclaimer: 本系统提供的信息仅供参考，不能替代专业医疗诊断与治疗建议。*
