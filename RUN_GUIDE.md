# 🚀 智能养老营养师 - 运行指南 (RUN_GUIDE.md)

本指南帮助您在本地环境快速部署和运行“智能养老营养师”系统，包括后端计算服务与前端交互界面。

## 📋 1. 环境准备

确保您的系统已安装以下基础环境：
- **操作系统**: Windows 10/11
- **Python**: 3.10 或更高版本
- **网络**: 能访问 DeepSeek API (https://api.deepseek.com)
- **Git** (可选，用于版本控制): [下载地址](https://git-scm.com/download/win)

## ⚙️ 2. 配置步骤

### 2.1 填写配置文件
系统首次运行会自动生成 `.env` 文件（从 `.env.example` 复制）。您需要手动编辑它：

1. 打开项目目录下的 `.env` 文件。
2. 填入您的 **DeepSeek API Key**：
   ```ini
   DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
   DEEPSEEK_API_BASE=https://api.deepseek.com/v1
   DEEPSEEK_MODEL=deepseek-chat
   ```
   *(注：如果您还没有 Key，请前往 DeepSeek 开放平台申请)*

### 2.2 安装依赖 (如果尚未安装)
如果您是第一次运行，建议手动安装/更新依赖：
```powershell
pip install -r requirements.txt
```

## ▶️ 3. 启动系统

### 方式一：Python 脚本启动 (推荐)
如果您希望使用 Python 来管理启动过程，我们提供了 **`run.py`** 脚本。
在终端中运行：
```bash
python run.py
```
该脚本会自动检测环境，并同时启动后端 API 和前端界面。

### 方式二：批处理脚本启动
直接双击项目目录下的 **`run_app.bat`** 脚本。

脚本会自动执行以下操作：
1. 检查并创建 `.env` 文件。
2. 创建必要的日志目录 `logs/`。
3. 启动 **后端 API 服务** (端口 8002)。
4. 启动 **前端 Streamlit 界面** (端口 8501)。

### 方式二：手动启动
如果脚本无法运行，您可以手动打开两个终端窗口：

**终端 1 (后端)**:
```bash
py -m uvicorn main:app --reload --port 8002
```

**终端 2 (前端)**:
```bash
py -m streamlit run app.py --server.port 8501
```

## 🔍 4. 验证运行

启动成功后，您可以通过以下地址访问：

- **用户界面 (UI)**: [http://localhost:8501](http://localhost:8501)
  - 在左侧栏设置年龄、慢病史（如高血压）。
  - 在对话框中提问：“高血压早餐吃什么？”
  
- **API 文档 (Swagger)**: [http://localhost:8002/docs](http://localhost:8002/docs)
  - 可在此测试 `/profile` 和 `/calculate_nutrition` 接口。

## 🛠️ 5. Dify 接入 (进阶)

如果您希望将本系统的计算能力接入 Dify 平台，请参考 **[DIFY_GUIDE.md](DIFY_GUIDE.md)**。
- 工具 Schema 地址: `http://localhost:8002/dify_tool.json`
- 知识库文件位置: `dify_assets/knowledge/`

## 📦 6. 版本控制与部署 (Git)

本项目已为您准备好 Git 配置文件 (`.gitignore`) 和一键初始化脚本。

### 6.1 初始化仓库
双击运行 **`init_git.bat`** 脚本，它会自动：
1. 检测 Git 是否安装。
2. 初始化本地仓库。
3. 添加所有文件（自动忽略敏感配置）。
4. 提交第一次 commit。

### 6.2 推送到 GitHub
1. 在 GitHub 上创建一个新仓库（不要勾选 Initialize with README）。
2. 在终端运行脚本提示的命令：
   ```bash
   git remote add origin <您的仓库地址>
   git branch -M main
   git push -u origin main
   ```

## ❓ 常见问题

**Q: 启动时提示 "DEEPSEEK_API_KEY not found"？**
A: 请检查 `.env` 文件是否已创建，并且 `DEEPSEEK_API_KEY` 字段已填入正确的值。

**Q: PowerShell 提示 "无法加载文件...禁止运行脚本"？**
A: 请以管理员身份运行 PowerShell，输入 `Set-ExecutionPolicy RemoteSigned` 解除限制，或使用 `powershell -ExecutionPolicy Bypass -File .\test_api.ps1` 运行测试脚本。
