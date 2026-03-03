# 基于大语言模型的养老智能营养师对话系统设计与实现

## 1. 摘要 (Abstract)
随着人口老龄化加剧，老年人的营养健康管理成为社会关注的焦点。本文设计并实现了一个基于大语言模型（LLM）的智能对话系统，旨在为老年用户提供个性化、科学且安全的膳食建议。系统通过多轮对话理解用户健康画像，结合专业营养学公式与慢病管理规则，利用 Prompt Engineering 技术生成针对性的饮食指导。

## 2. 系统架构 (System Architecture)

本系统支持灵活的架构部署，推荐使用 **Dify 平台** 作为统一的前端交互与智能编排引擎。

### 2.1 技术栈 (Dify 增强版)
- **前端与编排 (Frontend & Orchestration)**: Dify (Chatflow / Agent)
- **计算服务 (Backend Service)**: Python FastAPI (提供 RESTful Tool API)
- **智能核心 (AI Layer)**: Dify 内置 LLM (GPT-4/Claude/DeepSeek) + RAG
- **数据层 (Data Layer)**: Dify Knowledge Base (知识库) + 运行时变量

### 2.2 模块划分
1.  **Dify 应用层**:
    - **用户界面**: Dify WebApp 或嵌入式 Chat Widget。
    - **流程编排**: 
        - 输入解析 (Variables: Age, Height, Weight...)
        - 知识检索 (Knowledge Retrieval: 疾病饮食原则)
        - 工具调用 (Tool Call: 外部计算服务)
        - LLM 生成 (Prompt Engineering)
2.  **FastAPI 计算服务**:
    - **角色**: 退化为无状态的计算工具 (Stateless Tool)。
    - **接口**: 
        - `POST /calculate_nutrition`: 接收画像，返回 BMR/TDEE 及营养目标。
        - `GET /dify_tool.json`: 提供 OpenAPI Schema 供 Dify 自动接入。
3.  **知识库 (Knowledge Base)**:
    - 托管于 Dify 平台，存储结构化的营养学原则文本。
    - 支持语义检索与混合检索。

## 3. 核心算法与逻辑 (Core Algorithms)

### 3.1 动态营养目标计算
系统根据用户健康标签自动调整营养参数：
- **通用**: 蛋白 1.0-1.2g/kg，钠 < 2300mg。
- **高血压**: 钠 < 1500mg，增加钾摄入建议。
- **糖尿病**: 碳水占比 < 45%，限制精制糖。
- **慢性肾病 (CKD)**: 蛋白限制 0.6-0.8g/kg，关注磷/钾限制。

### 3.2 Prompt Engineering 策略
采用 "Role-Context-Instruction-Safety" 四段式结构：
- **Role**: 设定为“老年营养专家”，语气亲切、耐心。
- **Context**: 注入当前用户的完整画像与计算出的营养目标。
- **Knowledge**: (RAG) 注入相关的疾病饮食原则。
- **Safety**: 强制性医疗免责声明与急症就医指引。

## 4. 系统实现 (Implementation)

### 4.1 目录结构
```
smart_elderly_nutritionist/
├── app.py              # Streamlit 前端入口
├── main.py             # FastAPI 后端接口
├── models.py           # Pydantic 数据模型
├── utils.py            # 营养计算工具函数
├── prompts.py          # Prompt 模板与构建逻辑
├── llm_service.py      # LLM 接口封装与 RAG 实现
├── data/
│   └── knowledge.json  # 营养知识库
└── requirements.txt    # 项目依赖
```

### 4.2 关键代码片段 (LLM 调用)
```python
# llm_service.py (示意)
def get_response(self, request, context):
    # 1. 检索知识库
    relevant_knowledge = self.retrieve_knowledge(request.message)
    # 2. 构建 Prompt
    prompt = build_prompt(system_prompt, user_profile, relevant_knowledge, history)
    # 3. 调用 LLM
    response = self.client.chat.completions.create(messages=prompt)
    return response
```

## 5. 安全与伦理 (Safety & Ethics)
- **数据隐私**: 敏感健康数据仅在会话期间处理，MVP阶段不持久化存储，生产环境需加密。
- **医疗边界**: 系统严格限制在“健康咨询”范畴，对于涉及诊断、处方调整的问题，通过关键词匹配（如“胸痛”、“停药”）触发拒绝回答机制。
- **适老化设计**: 界面字体大、对比度高，语言通俗易懂，支持模糊意图理解。

## 6. 总结与展望
本系统实现了一个垂直领域的智能营养师 MVP。未来计划引入向量数据库提升检索精度，增加多模态输入（如拍照识别食物），并接入真实的医院/体检数据接口，打造全生命周期的老年健康管理平台。
