# Dify 平台接入指南 (DIFY_GUIDE.md)

本指南帮助您将「智能养老营养师」后端计算能力与知识库接入 Dify 平台，利用 Dify 强大的编排能力构建前端应用。

## 1. 架构调整
- **原架构**: Streamlit (前端) -> FastAPI (后端 + LLM + RAG)
- **新架构**: Dify (前端 + 编排 + LLM + RAG) -> FastAPI (作为外部工具提供营养计算)

## 2. 准备工作
1. 确保本地 FastAPI 服务已启动 (`run_app.bat` 中的后端部分)。
2. 确保 Dify 能够访问本机网络（如果是 Docker 部署的 Dify，需使用 `host.docker.internal`）。

## 3. 接入步骤

### 第一步：创建自定义工具 (Custom Tool)
Dify 需要通过 API 调用我们的后端来计算 BMR、TDEE 和营养目标。

1. 在 Dify 导航栏选择 **工具 (Tools)** -> **自定义 (Custom)** -> **创建自定义工具**。
2. **名称**: `nutrition_calculator`
3. **Schema 内容**: 
   - 访问 `http://localhost:8000/dify_tool.json`
   - 复制返回的 JSON 内容。
   - 粘贴到 Dify 的 Schema 编辑框中。
   - **注意**: 如果 Dify 是 Docker 部署，请确保 Schema 中的 `servers.url` 为 `http://host.docker.internal:8000` (代码已默认处理)。如果是云端 Dify，则需要将本地 API 部署到公网 (如使用 Ngrok)。
4. 点击 **保存**。

### 第二步：创建知识库 (Knowledge Base)
建议创建一个统一的“老年营养知识库”，包含多个专业文档。

1. **上传文件**:
   - 访问 `dify_assets/knowledge/` 目录。
   - 选中并上传所有 Markdown 文件：
     - `guide_general_elderly.md` (一般与高龄指南)
     - `guide_hypertension.md` (高血压/DASH)
     - `guide_diabetes.md` (糖尿病/GI)
     - `guide_gout.md` (痛风/低嘌呤)
     - `guide_ckd.md` (慢性肾病/低蛋白)
     - `guide_drug_interactions.md` (药物相互作用速查)

2. **分段设置 (Segmentation)**:
   - 模式: **自动分段与清洗 (Automatic)**。
   - 规则: 建议分段长度 **500-800 tokens**，重叠 **50 tokens**。
   - 索引方式: **高质量 (High Quality)** - 使用 Embedding 模型。

3. **检索设置 (Retrieval)**:
   - **混合检索 (Hybrid Search)** (推荐): 同时使用关键词匹配和向量检索，开启 **Rerank** 模型（如 BGE-Reranker）以提高精准度。
   - **Top K**: 建议设置为 **3-5**，避免上下文过长干扰 LLM。

### 第三步：创建应用 (Create App)
1. 创建一个 **聊天助手 (Chatbot)** 应用。
2. **编排模式**: 建议选择 **Agent** 模式或 **Chatflow** 模式（更灵活）。

#### 方式 A：Agent 模式配置
- **提示词 (System Prompt)**:
  复制 `prompts.py` 中的 `SYSTEM_PROMPT` 内容，并做微调：
  ```markdown
  你是“智能养老营养师助手”... (保留原内容)
  
  请在回答前，先调用 `calculate_nutrition` 工具获取用户的营养目标，并检索知识库中的相关饮食建议。
  ```
- **上下文 (Context)**: 关联刚才创建的“养老营养知识库”。
- **工具 (Tools)**: 添加 `nutrition_calculator` 工具。

#### 方式 B：Chatflow 模式配置 (推荐)
构建如下工作流：
1. **开始节点**: 定义输入变量 `age`, `height`, `weight`, `conditions` 等。
2. **问题分类节点**: 添加一个“问题分类器 (Question Classifier)”，定义 4-5 个分类（见 `dify_assets/intent_classification.md`）。
   - **EMERGENCY**: 紧急/急症 -> 连接到 **安全警示回复节点**。
   - **DIET_QUERY**: 饮食咨询 -> 连接到 **知识检索节点**。
   - **MEAL_PLAN**: 食谱生成 -> 连接到 **工具节点**。
   - **CHITCHAT**: 闲聊 -> 连接到 **LLM节点 (情感陪伴)**。
   - **IRRELEVANT**: 无关话题 -> 连接到 **拒绝回复节点**。
3. **安全警示回复节点**:
   - 直接输出：**"请注意：如果您出现胸痛、呼吸困难或剧烈不适，请立即停止咨询，拨打120或前往医院急诊。我不提供医疗诊断服务。"**
4. **拒绝回复节点**:
   - 直接输出：**"您好！我是专注于老年营养健康的助手。关于您提到的问题（如投资、政治等），超出了我的专业范围。如果您有关于高血压饮食、糖尿病食谱或日常营养的问题，我很乐意为您解答！"**
5. **知识检索节点**: 输入用户问题，检索知识库。
5. **工具节点**: 调用 `calculate_nutrition`，传入画像变量。
6. **LLM 节点**:
   - System Prompt: 设定角色。
   - User Prompt: 组合工具输出的 `summary` (营养目标) + 检索到的 `context` + 用户问题。
7. **回复节点**: 输出 LLM 的结果。

### 4. 高级编排：意图识别与分流
为了提升用户体验，建议参考 `dify_assets/intent_classification.md` 中的分类体系。
- **紧急意图 (EMERGENCY)** 是最高优先级的安全护栏，必须前置拦截。
- **画像更新 (PROFILE_UPDATE)** 可以引导用户去修改侧边栏表单，而不是在对话中处理复杂的字段提取。

## 5. 常见问题
- **Dify 报错 "Connection refused"**: 
  - 检查 FastAPI 是否运行。
  - 检查 Dify 容器是否能访问宿主机端口（尝试 `host.docker.internal`）。
- **Schema 解析错误**: 
  - 确保复制的是 `http://localhost:8000/dify_tool.json` 的完整 JSON 响应。

## 5. 文件清单
- `dify_assets/knowledge_base.txt`: 知识库源文件。
- `main.py`: 已更新，提供 `/dify_tool.json` 接口。
