# LinguaLoop

LinguaLoop 是一个开源的对话式语言学习平台。项目目标是把「真实输入 + 可控对话 + 即时反馈 + 复盘练习」组织成一个持续学习闭环，而不是只做聊天机器人或单词本。

## 当前状态

项目处于初始化阶段。本仓库目前包含基础文档、Python core 的早期脚手架、CLI POC，以及一个最小桌面端 POC，用于沉淀产品边界、MVP 范围、架构方向和协作规范。

## 产品方向

LinguaLoop 面向已经有一定输入材料的学习者，例如视频字幕、播客转写、文章、聊天记录或课程笔记。系统会围绕这些材料生成可追踪的学习会话，帮助用户完成理解、对话、纠错、复述和复习。

核心学习闭环：

1. 导入真实语言材料
2. 提取词汇、表达、语法和话题
3. 生成分级对话任务
4. 在对话中即时纠错和提示
5. 形成复盘卡片与下次练习计划

## 文档导航

- [AGENTS.md](./AGENTS.md): 给 Codex / coding agents 的仓库工作规则
- [docs/README.md](./docs/README.md): 文档目录入口和分类导航
- [docs/product/PROJECT_BRIEF.md](./docs/product/PROJECT_BRIEF.md): 项目愿景、用户和产品原则
- [docs/product/MVP_SPEC.md](./docs/product/MVP_SPEC.md): 第一版 MVP 范围和验收标准
- [docs/architecture/ARCHITECTURE.md](./docs/architecture/ARCHITECTURE.md): 初始系统架构和模块边界
- [docs/architecture/CORE_CONCEPTS.md](./docs/architecture/CORE_CONCEPTS.md): Core 领域对象、Provider、EventStore 和 Python/Pydantic 基础概念
- [docs/architecture/PLUGIN_ARCHITECTURE.md](./docs/architecture/PLUGIN_ARCHITECTURE.md): Core / Plugins / Patterns 三层扩展架构
- [docs/architecture/AGENT_CORE_ARCHITECTURE.md](./docs/architecture/AGENT_CORE_ARCHITECTURE.md): Python-first Agent Kernel、LangGraph adapter 和 typed LLM 调用规划
- [docs/decisions/TECH_DECISIONS.md](./docs/decisions/TECH_DECISIONS.md): 技术决策记录和待定项
- [docs/planning/ROADMAP.md](./docs/planning/ROADMAP.md): 开发路线图
- [CONTRIBUTING.md](./CONTRIBUTING.md): 开源贡献规范

## 本地验证

安装开发依赖后，可以运行当前 core 测试：

```bash
python -m pytest
```

## 下一步

建议先完成以下决策，再创建应用脚手架：

1. 选择第一版前端形态：Web app、桌面 app，或移动优先 PWA
2. 确认 Python-first Agent Kernel 方案，并决定何时接入 LangGraph adapter
3. 选择第一版后端形态：FastAPI 服务、本地优先应用，或其他 Python API surface
4. 明确第一版 LLM 接入策略：PydanticAI adapter、兼容 OpenAI 的 provider，或轻量自写 adapter
5. 定义插件 manifest、Pattern contract、capability requirements 和权限模型
6. 确定开源许可证

## 真实 AI 冒烟测试

默认 `python -m pytest` 不应调用真实模型。要测试从 LangGraph 到 OpenAI-compatible provider 再到真实模型的完整链路，请在本地 `.env` 配置：

```dotenv
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.centos.hk/v1
OPENAI_REASONING_MODEL=your_reasoning_model_id
OPENAI_DIALOGUE_MODEL=your_dialogue_model_id
OPENAI_DISABLE_THINKING=1
RUN_REAL_AI_TESTS=1
```

如果不确定中转站可用模型名，先运行：

```powershell
.venv\Scripts\python.exe scripts\list_openai_models.py
```

再把返回列表里的模型 id 填到 `OPENAI_REASONING_MODEL` 和 `OPENAI_DIALOGUE_MODEL`。然后运行真实 AI 冒烟测试：

```powershell
.venv\Scripts\python.exe -m pytest tests\test_llm.py -q
```

不要提交 `.env` 文件；仓库已在 `.gitignore` 中忽略本地环境文件。

## CLI POC

现在已经有一个无 UI 的命令行原型，可以先验证完整闭环：

```powershell
lingualoop --mock
```

如果还没把项目同步进当前环境，先执行 `uv sync --dev`，或者临时用 `PYTHONPATH=src` 再运行。

常用命令：

- `load`：加载并分析材料
- `start`：开始一次练习会话
- `say`：发送用户回答
- `review`：查看复习项
- `summary`：查看当前会话摘要
- `export`：导出会话 JSON
- `reset`：清空当前状态
- `quit`：退出

默认模式会读取 `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_REASONING_MODEL` 和 `OPENAI_DIALOGUE_MODEL`。离线调试可用 `--mock`。

## Desktop POC

桌面端当前采用 `PySide6 + QML + Qt Quick Controls 6 + KDE Kirigami`。PySide6 通过 Python 依赖安装，Kirigami 需要系统或平台提供对应的 `org.kde.kirigami` QML runtime：

```powershell
uv sync --extra desktop
```

启动最小桌面壳。桌面端默认使用真实 OpenAI-compatible provider，并读取当前工作目录 `.env` 或系统环境变量中的 `OPENAI_*` 配置：

```powershell
uv run lingualoop-desktop
```

离线调试时可以显式使用 mock provider，不需要真实 API key：

```powershell
uv run lingualoop-desktop --mock
```

桌面端默认中文界面。当前桌面端是共享桌面/Android 页面和最小学习闭环的 POC，不代表最终 UI 或完整客户端功能。Kirigami runtime 的平台要求见 [docs/desktop/QML_RUNTIME.md](./docs/desktop/QML_RUNTIME.md)。

Windows 用户可按 [QML runtime 文档](./docs/desktop/QML_RUNTIME.md) 安装 KDE Craft 和 Kirigami。仓库提供 `scripts/setup_kirigami_windows.ps1` 自动发现 Craft runtime 并配置 QML import path。
