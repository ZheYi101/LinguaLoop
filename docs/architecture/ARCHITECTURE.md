# Architecture

## 初始架构目标

第一版架构应支持快速验证产品闭环，同时保留 LLM provider、存储层和前端形态的替换空间。不要为了早期 MVP 引入过重的分布式架构。

核心和 agent kernel 采用 Python-first 方向。前端形态仍可独立选择，但领域模型、Pattern、Plugin capability、Agent Kernel 和第一批 provider adapter 应优先用 Python 编写。

## 建议模块边界

```text
apps
  web app
  desktop / Android QML surfaces

client
  UI components
  conversation view
  material editor
  review dashboard

QML UI
  Python QObject ViewModel
    LearningWorkbench
      Kernel / Provider

application
  material analysis use cases
  practice session orchestration
  feedback and review generation

agent-kernel
  PatternRunner
  CapabilityRegistry
  AgentEngine protocol
  SessionCoordinator
  GraphCompiler

engine-adapters
  LangGraph adapter
  direct deterministic runner for tests

domain
  learning material
  practice session
  feedback item
  review item
  user preferences
  pattern contracts
  session event schema

plugin-runtime
  plugin manifest
  capability registry
  lifecycle hooks
  permissions and configuration

infrastructure
  persistence
  LLM provider adapters
  auth adapter
  telemetry / logging

plugins
  voice providers
  avatar renderers
  importers
  LLM / STT / TTS providers

patterns
  roleplay
  shadowing
  retell
  socratic
  spaced review
```

## 插件化原则

LinguaLoop 应采用 `fixed learning core + optional plugins + capability-aware patterns`，而不是把整个产品设计成 `everything is plugin`。

Core 负责定义学习语义、状态机、事件日志、Pattern contract、capability contract 和结构化输出。Plugins 负责扩展可选能力，例如语音、Live2D、材料导入、LLM/STT/TTS provider。Patterns 负责组织学习流程，并通过 capability requirements 声明自己依赖哪些插件能力。插件不得绕过 core schema 直接改写用户学习数据。

详细设计见 [PLUGIN_ARCHITECTURE.md](./PLUGIN_ARCHITECTURE.md)。Pattern 分类见 [LEARNING_PATTERNS.md](./LEARNING_PATTERNS.md)。Core 对象和基础概念见 [CORE_CONCEPTS.md](./CORE_CONCEPTS.md)。

Agent kernel 详细设计见 [AGENT_CORE_ARCHITECTURE.md](./AGENT_CORE_ARCHITECTURE.md)。

## Agent Kernel 原则

LinguaLoop 的核心 agent 不是一个自由规划的大 agent，而是一个领域化学习流程执行器。它不负责像 Codex 或 Claude Code 那样自主解决任意任务；它负责执行可声明、可测试、可复盘的语言学习 Pattern。

系统的灵活度主要放在 Pattern 层：Pattern 固定练习模式、语境、纠错强度、输入 modality、结束条件、复习项生成和复习节奏。Kernel 负责执行 Pattern、检查 capability、调用 provider、记录 `SessionEvent`，并把输出沉淀为 `FeedbackItem` 和 `ReviewItem`。

默认 runtime adapter 采用 LangGraph，但 Core 不依赖 LangGraph。LangGraph 负责 stateful workflow、conditional routing、streaming 和 checkpoint / resume；LinguaLoop 自己负责领域模型、Pattern contract、capability registry、权限和事件语义。

## 学习材料生命周期

经验工作区显示，输入材料在进入练习前需要经历清晰生命周期，而不是从用户粘贴文本直接跳到对话：

```text
RawSource
  -> NormalizedMaterial
  -> LearningSegment
  -> PracticePlan
  -> PracticeSession
  -> FeedbackItem / ReviewItem
```

- `RawSource` 保存用户导入或粘贴的原始材料。
- `NormalizedMaterial` 表示去除字幕编号、时间戳、重复 cue、断行和明显噪音后的 lesson-ready text。
- `LearningSegment` 是可教学片段，带有 `track`、`start_ref`、`end_ref`、`scene_or_argument_summary`、前后文摘要等元数据。
- `PracticePlan` 由 Pattern 生成，决定本轮怎么练。
- `PracticeSession` 聚合当前会话状态，但长期事实应由 `SessionEvent` 保存。

这个生命周期支持后续材料导入插件、不同 track 的切分策略，以及 review 时不必重新读取完整原材料也能恢复语境。

## 学习证据与状态

LinguaLoop 不应把“内容展示过”当成“学习者掌握了”。学习状态只能由真实表现证据推进：用户回答、冷启动输出、纠错结果、复习结果、延迟检索结果和用户控制动作。

因此持久化层应区分：

- `SessionEvent`: 发生过的事实，是可回放学习历史。
- `FeedbackItem`: 从用户输出中产生的纠错证据。
- `ReviewItem`: 未来要重新检索或迁移使用的任务。
- `LearnerProfile`: 从历史证据汇总出的当前快照，不是唯一事实来源。

详细方法依据见 [Learning Loop Foundation](../research/LEARNING_LOOP_FOUNDATION.md) 和 [Practice Workspace Findings](../research/PRACTICE_WORKSPACE_FINDINGS.md)。

## LLM 编排原则

- Prompt 不应直接散落在 UI 组件中。
- Provider adapter 返回结构化结果，业务层负责校验和回退。
- 每个 LLM 任务应有明确输入、输出 schema 和失败策略。
- 对话消息、纠错项和复盘项应能关联回原始材料或会话片段。
- PydanticAI 可作为第一批 typed LLM call adapter，但不要让业务层直接依赖 PydanticAI agent 对象。

## QML UI 边界

桌面端和 Android 端使用 PySide6 加载 QML。Qt Quick Controls 6 提供基础控件，Kirigami 提供 ApplicationWindow、Page、导航和响应式布局。QML 不接触领域模型、LangGraph 或具体 provider；Python ViewModel 将领域对象转换为稳定的字符串、列表和状态属性。

材料、练习和复盘是独立页面。桌面端可以使用更宽的上下文区域，移动端使用单列 PageStack/滚动布局。网络操作必须在 Python worker/thread 中执行，ViewModel 通过 busy/error/result signals 更新 QML。

## 语音与实时对话

LiveKit 是 `voice-livekit` 插件的强候选 SDK，而不是项目总基座。Core 只依赖 `VoiceSessionProvider` / capability 抽象，语音插件内部处理 WebRTC、turn detection、interruption、STT-LLM-TTS pipeline、实时转录和延迟指标。依赖语音的 Pattern 只声明 `voice.session`、`stt.transcribe` 或 `tts.speak`，不直接绑定 LiveKit。

第一版文本 MVP 不把语音放在关键路径，但架构应保留语音插件接入点。

## 关键用例

- analyzeMaterial(material): 生成摘要、关键词、表达点和练习建议。
- startPracticeSession(material, goal, preferences): 创建练习会话。
- continueConversation(session, userMessage): 生成下一轮 AI 回复和可选反馈。
- summarizeSession(session): 生成复盘和 review items。
- startReview(language, profile, reviewQueue): summary-first 地选择 1-3 个复习方向，而不是直接倾倒所有过期条目。
- recordLearningEvidence(session, event): 把用户输出、反馈、复习结果和用户控制动作保存为可回放事件。

## 数据与隐私

- 用户导入的语言材料可能包含私人内容，默认按敏感数据处理。
- 日志中不得记录完整原文、完整对话或密钥。
- 若后续支持云同步，需要明确数据保留、删除和导出机制。
- 本地开发应使用 `.env.example` 描述环境变量，不提交 `.env`。

## 待定架构问题

- 前端是否采用 Next.js、Vite SPA，还是其他形态。
- 后端是否采用同构应用 API routes、独立 API 服务，还是 BaaS。
- 持久化是否先用 SQLite/Postgres，还是本地文件/浏览器存储。
- 是否从第一版就支持多 LLM provider。
- 插件 manifest、权限模型和版本兼容策略如何设计。
- Pattern manifest、capability requirements 和 fallback 策略如何设计。
- `voice-livekit` 是否作为第一批官方插件实现，还是等文本闭环跑通后再实现。
- LangGraph adapter 在 MVP 中何时替换 direct deterministic runner。
