# Architecture

## 初始架构目标

第一版架构应支持快速验证产品闭环，同时保留 LLM provider、存储层和前端形态的替换空间。不要为了早期 MVP 引入过重的分布式架构。

核心和 agent kernel 采用 Python-first 方向。前端形态仍可独立选择，但领域模型、Pattern、Plugin capability、Agent Kernel 和第一批 provider adapter 应优先用 Python 编写。

## 建议模块边界

```text
apps
  web app
  future desktop / mobile surfaces

client
  UI components
  conversation view
  material editor
  review dashboard

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

详细设计见 [PLUGIN_ARCHITECTURE.md](./PLUGIN_ARCHITECTURE.md)。

Agent kernel 详细设计见 [AGENT_CORE_ARCHITECTURE.md](./AGENT_CORE_ARCHITECTURE.md)。

## Agent Kernel 原则

LinguaLoop 的核心 agent 不是一个自由规划的大 agent，而是一个学习流程执行器。它把 Pattern 产出的 `PracticePlan` 编译为可执行、可暂停、可复盘的 agent flow，并把每一步输出落成 `SessionEvent`、`FeedbackItem` 和 `ReviewItem`。

默认 runtime adapter 采用 LangGraph，但 Core 不依赖 LangGraph。LangGraph 负责 stateful workflow、conditional routing、streaming 和 checkpoint / resume；LinguaLoop 自己负责领域模型、Pattern contract、capability registry、权限和事件语义。

## LLM 编排原则

- Prompt 不应直接散落在 UI 组件中。
- Provider adapter 返回结构化结果，业务层负责校验和回退。
- 每个 LLM 任务应有明确输入、输出 schema 和失败策略。
- 对话消息、纠错项和复盘项应能关联回原始材料或会话片段。
- PydanticAI 可作为第一批 typed LLM call adapter，但不要让业务层直接依赖 PydanticAI agent 对象。

## 语音与实时对话

LiveKit 是 `voice-livekit` 插件的强候选 SDK，而不是项目总基座。Core 只依赖 `VoiceSessionProvider` / capability 抽象，语音插件内部处理 WebRTC、turn detection、interruption、STT-LLM-TTS pipeline、实时转录和延迟指标。依赖语音的 Pattern 只声明 `voice.session`、`stt.transcribe` 或 `tts.speak`，不直接绑定 LiveKit。

第一版文本 MVP 不把语音放在关键路径，但架构应保留语音插件接入点。

## 关键用例

- analyzeMaterial(material): 生成摘要、关键词、表达点和练习建议。
- startPracticeSession(material, goal, preferences): 创建练习会话。
- continueConversation(session, userMessage): 生成下一轮 AI 回复和可选反馈。
- summarizeSession(session): 生成复盘和 review items。

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
