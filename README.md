# LinguaLoop

LinguaLoop 是一个开源的对话式语言学习平台。项目目标是把「真实输入 + 可控对话 + 即时反馈 + 复盘练习」组织成一个持续学习闭环，而不是只做聊天机器人或单词本。

## 当前状态

项目处于早期 MVP 阶段。本仓库目前包含基础文档、Python core、CLI POC，以及 PySide6/QML 桌面端工作台。当前闭环已支持本地 SQLite 持久化、Markdown/DOCX 材料导入、多轮材料对话、用户主动结束复盘、review queue 和基础复习结果记录。

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

安装开发依赖后，可以运行当前测试：

```bash
python -m pytest
```

使用 `uv` 时推荐：

```powershell
uv sync --dev --extra desktop
.venv\Scripts\python.exe -m pytest -q
```

## 下一步

建议优先打磨以下能力：

1. 将当前 direct runner 抽成正式内置 Pattern。
2. 完善材料 segment metadata 和 review source linking。
3. 增加更完整的复习页交互和 review outcome 历史展示。
4. 补齐插件 manifest、Pattern contract、capability requirements 和权限模型。
5. 确定开源许可证。

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
- `import`：导入 `.md`、`.markdown` 或 `.docx` 材料
- `start`：开始一次练习会话
- `say`：发送用户回答
- `finish`：结束本轮并生成结构化复盘和 review items
- `review`：查看复习项
- `rate`：记录 `again`、`hard`、`good` 或 `easy` 复习结果
- `summary`：查看当前会话摘要
- `export`：导出会话 JSON
- `reset`：清空当前选择状态，不删除本地持久化数据
- `quit`：退出

默认模式会读取 `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_REASONING_MODEL` 和 `OPENAI_DIALOGUE_MODEL`。离线调试可用 `--mock`。

## Desktop POC

桌面端当前采用 `PySide6 + QML + Qt Quick Controls 6 + KDE Kirigami`。PySide6 通过 Python 依赖安装，Kirigami 需要系统或平台提供对应的 `org.kde.kirigami` QML runtime：

```powershell
uv sync --extra desktop
```

启动桌面工作台。桌面端默认使用真实 OpenAI-compatible provider，并读取当前工作目录 `.env` 或系统环境变量中的 `OPENAI_*` 配置：

```powershell
uv run lingualoop-desktop
```

离线调试时可以显式使用 mock provider，不需要真实 API key：

```powershell
uv run lingualoop-desktop --mock
```

桌面端默认中文界面，采用左导航、中工作区、右上下文的三栏布局；窄屏会折叠为单列导航。默认本地数据保存在平台应用数据目录下的 `LinguaLoop/lingualoop.sqlite3`，也可通过 `LINGUALOOP_DATA_DIR` 覆盖。Kirigami runtime 的平台要求见 [docs/desktop/QML_RUNTIME.md](./docs/desktop/QML_RUNTIME.md)。

Windows 用户可按 [QML runtime 文档](./docs/desktop/QML_RUNTIME.md) 安装 KDE Craft 和 Kirigami。仓库提供 `scripts/setup_kirigami_windows.ps1` 自动发现 Craft runtime 并配置 QML import path。
