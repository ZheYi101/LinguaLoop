# LinguaLoop

LinguaLoop 是一个开源的对话式语言学习平台。项目目标是把「真实输入 + 可控对话 + 即时反馈 + 复盘练习」组织成一个持续学习闭环，而不是只做聊天机器人或单词本。

## 当前状态

项目处于初始化阶段。本仓库目前包含基础文档和 Python core 的早期脚手架，用于沉淀产品边界、MVP 范围、架构方向和协作规范。正式应用尚未创建。

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
