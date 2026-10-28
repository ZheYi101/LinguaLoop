# 文档目录

本文档目录按读者意图分类。新文档优先放入对应子目录，避免所有内容堆在 `docs/` 根目录。

当前主旨是“沉浸提供语境、语音对话练输出”。产品定位以 Project Brief 为准，验收边界以 MVP Spec 为准，交付顺序见 Roadmap；历史决策和研究样本中的文本 MVP 路径不覆盖当前范围。

## Product

- [Project Brief](./product/PROJECT_BRIEF.md): 当前产品主旨、沉浸到语音输出的核心体验、产品原则和未决项。
- [MVP Spec](./product/MVP_SPEC.md): 文本原型与正式语音 MVP 的边界、用户故事和验收标准。
- [UI Surface Plan](./product/UI_SURFACE_PLAN.md): MD3 主题、材料与对话主入口、辅助入口和自适应导航。

## Research

- [Learning Loop Foundation](./research/LEARNING_LOOP_FOUNDATION.md): 语言学习闭环的理论基础、实践约束和架构含义。
- [Practice Workspace Findings](./research/PRACTICE_WORKSPACE_FINDINGS.md): 从既有 input-driven skill 和 EnglishLearningWorkflow 经验样本中提取的产品与数据模型经验。
- [服务选型与实施边界](./research/SERVICE_SELECTION_2026-10-24.md): DeepSeek 模型契约、国内中日语 STT/TTS、本地语音候选，以及 RTC 后续最小流式接入与无新增费用的验证路径。
- [材料整理与快速对话参考方案评审](./research/REFERENCE_PLAN_REVIEW_2026-10-24.md): 用户参考 DOCX 与当前实现的对照、证据和预测指标边界。

## Architecture

- [Architecture](./architecture/ARCHITECTURE.md): 初始系统架构、模块边界和关键用例。
- [Agent Core Architecture](./architecture/AGENT_CORE_ARCHITECTURE.md): Python-first Agent Kernel、LangGraph adapter 和 typed LLM 调用规划。
- [Extension Architecture](./architecture/PLUGIN_ARCHITECTURE.md): Core / Plugins / Patterns 三层扩展架构。
- [Learning Patterns](./architecture/LEARNING_PATTERNS.md): input lesson、guided roleplay、review、CORA 等学习 Pattern 的分类和共同不变量。
- [Core Concepts](./architecture/CORE_CONCEPTS.md): 当前 `src/lingualoop/core` 中核心模型、Provider、EventStore 和常见 Python/Pydantic 写法说明。

## Planning

- [Roadmap](./planning/ROADMAP.md): 从已有文本原型到核心语音 MVP、后续增强和开源协作的开发路线图。
- [真实小说验收](./planning/NOVEL_ACCEPTANCE_2026-10-28.md): 完整《Lolita》30 段准备、截断修复、余额阻塞和待完成的真实读者式讨论；不将分段准备或离线测试当作文本验收通过。
- [初版验证记录](./planning/INITIAL_VERSION_2026-10-24.md): 本次交付、验证证据与真实语音未决项。
- [双模型文本独立验收](./planning/TEXT_ACCEPTANCE_2026-10-24.md): 有界真实 HTTP、后台准备消费、延迟与离线/分发验证证据。
- [代码独立审查](./planning/CODE_AUDIT_2026-10-24.md): 独立审查发现、修复和验证范围。

## Decisions

- [Technical Decisions](./decisions/TECH_DECISIONS.md): 会影响长期维护的技术决策记录。
- [QML Runtime](./desktop/QML_RUNTIME.md): PySide6、Kirigami QML module 和平台运行要求。
- [分轮语音](./desktop/VOICE.md): 独立 STT/TTS 环境配置、数据边界与真人三轮验收。
- [LiveKit 本机探针](./desktop/LIVEKIT.md): 可选 RTC extra、loopback 范围、文本/PCM 轮次协议、连接失败与资源清理证据。

## Root Documents

- [Repository Guide](../AGENTS.md): coding agents 的仓库工作约定。
- [Contributing](../CONTRIBUTING.md): 开源贡献规范。
