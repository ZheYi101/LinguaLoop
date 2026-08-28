# Technical Decisions

本文档记录会影响长期维护的技术选择。当前项目尚未锁定技术栈，以下为初始建议和待定项。

## Decision 0001: 先文档化范围，再脚手架化应用

- Status: Accepted
- Date: 2026-08-14

### 背景

项目仍处于产品和工程边界定义阶段。如果过早创建完整脚手架，容易把技术栈选择固化在尚未验证的产品假设上。

### 决策

先建立 README、AGENTS、MVP、架构和路线图等基础文档。后续在明确第一版交互形态、存储方式和 LLM 接入方式后，再创建应用代码。

### 影响

- 短期没有可运行应用。
- 后续脚手架应以 `docs/MVP_SPEC.md` 和 `docs/ARCHITECTURE.md` 为事实来源。
- 技术栈选择需要在本文档中补充新的 decision entry。

## Decision 0002: 采用 Core / Plugins / Patterns 三层扩展架构

- Status: Accepted
- Date: 2026-08-25

### 背景

项目希望支持语音、Live2D、不同学习 pattern、复习调度、材料导入、LLM/STT/TTS provider 等能力扩展。DeepSeek Harness 展示了一种高度插件化的 agent harness 设计：通过插件贡献模型、工具、session log、agent loop、UI 等能力。

LinguaLoop 可以借鉴这种插件组合思想，但产品目标不同。LinguaLoop 的核心价值来自稳定学习闭环，而不是任意 agent 能力组合。学习 Pattern 也不应被混同为普通能力插件：Pattern 负责「怎么学」，Plugin 负责「能做什么」。

### 决策

LinguaLoop 采用 `fixed learning core + optional plugins + capability-aware patterns`。

- Core 定义学习材料、练习会话、消息、反馈、复习项、session events、Pattern contract、capability contract 和结构化输出。
- Plugins 是可用可不用的能力提供者，例如语音、Live2D、材料导入、LLM/STT/TTS provider。
- Patterns 是可组合的学习流程，例如 roleplay、shadowing、retell、spaced-review。Pattern 可以依赖特定 capability，但不直接依赖具体插件实现。

插件通过明确 contract 扩展能力，不能直接改写 core schema 或绕过学习状态机。Pattern 通过 capability requirements 声明运行条件。

DeepSeek Harness 可以作为参考和实验性 adapter，但不作为 LinguaLoop 的总基座。

### 影响

- 需要新增 `plugin-runtime`、`plugins` 和 `patterns` 的架构边界。
- 语音、Live2D、provider、importer 作为插件能力设计。
- 学习 Pattern 作为独立流程层设计，可声明对插件 capability 的依赖。
- MVP 仍先验证文本学习闭环，只实现最小 plugin registry、capability requirement check 和一个内置文本 Pattern。
- 插件权限、Pattern fallback、版本兼容、事件命名空间和 schema 校验会成为早期基础设施工作。

### 参考

- DeepSeek Harness architecture: https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md
- Cordis tutorial in DeepSeek Harness: https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/cordis-tutorial/index.md

## Decision 0003: LiveKit 作为语音插件 SDK，而不是项目总基座

- Status: Accepted
- Date: 2026-08-25

### 背景

LinguaLoop 后续可能发展出口语 AI 对话、实时转录、用户打断、turn detection、流式 TTS、语音延迟指标等能力。LiveKit Agents 和 LiveKit SDK 适合处理实时音频、WebRTC、room/session、provider integrations 和语音 agent pipeline。

但 LiveKit 不定义 LinguaLoop 的学习材料、练习策略、复盘结构或复习机制。

### 决策

LiveKit 作为 `voice-livekit` 插件的底层 SDK / runtime dependency。Core 只定义 `VoiceSessionProvider` / voice capability 抽象，应用层和 Pattern 通过插件注册的能力使用语音会话。

```text
LinguaLoop core
  -> VoiceSessionProvider contract
    -> voice-livekit plugin
      -> LiveKit Agents / LiveKit SDK / selected STT-LLM-TTS providers
```

### 影响

- 文本 MVP 不被 LiveKit 复杂度阻塞。
- 未来可以替换或并存 OpenAI Realtime API、Gemini Live API、Pipecat 或其他语音方案。
- 学习领域模型不会被 room / participant / track 等实时通信模型污染。
- 语音插件需要单独追踪用户停说到 AI 出声、打断响应、STT partial 稳定性、TTS 首音频和单轮成本。
- 依赖语音的 Pattern 只声明 voice / STT / TTS capability，不感知 LiveKit 细节。

### 参考

- LiveKit Agents introduction: https://docs.livekit.io/agents/
- LiveKit model plugins: https://docs.livekit.io/agents/models/
- LiveKit turn detection and interruptions: https://docs.livekit.io/agents/logic/turns/
- LiveKit pipeline nodes and hooks: https://docs.livekit.io/agents/logic/nodes/

## Decision 0004: Python-first Agent Kernel with LangGraph Adapter

- Status: Accepted
- Date: 2026-08-27

### 背景

项目主语言倾向 Python。核心 agent 层需要支持 Pattern 执行、插件能力调用、结构化输出、可恢复会话、事件记录和后续语音扩展。如果不用 DeepSeek Harness，不代表要重写完整 harness；LinguaLoop 需要自有的是学习领域内核和一层薄 agent kernel。

### 决策

采用 Python-first 核心架构：

- Core 使用 Pydantic models 定义领域对象、事件、Pattern contract 和 capability contract。
- Agent Kernel 手写 `PatternRunner`、`CapabilityRegistry`、`SessionCoordinator`、`AgentEngine` protocol 和 `EventStore` interface。
- 默认 `AgentEngine` adapter 使用 LangGraph，负责 stateful workflow、routing、streaming、checkpoint / resume。
- typed LLM calls 使用 PydanticAI 或轻量 Pydantic provider adapter，统一包在 LinguaLoop 的 `TypedLLMClient` 后面。
- LiveKit 继续作为 `voice-livekit` 插件的 SDK，不进入 Core 或 Agent Kernel。

### 影响

- 不采用 DeepSeek Harness 作为主 runtime，但保留实验性 adapter 的可能。
- 第一阶段先实现 direct deterministic runner，确保手写核心可理解、可测试；LangGraph adapter 在同一 flow 稳定后接入。
- Core 和 Kernel 不直接暴露 LangGraph checkpoint、PydanticAI agent 或 LiveKit room 概念。
- 项目默认语言约定从 TypeScript-first 调整为 Python-first core；前端可独立选择 TypeScript / Web 技术栈。
- 初始 Python package scaffold 已创建，LangGraph 先作为 `engine.langgraph` adapter 引入，core 只保留领域模型和 provider contract。

### 参考

- LangGraph overview: https://docs.langchain.com/oss/python/langgraph/overview
- LangGraph graph API: https://docs.langchain.com/oss/python/langgraph/graph-api
- PydanticAI agents: https://pydantic.dev/docs/ai/core-concepts/agent/
- PydanticAI output validation: https://pydantic.dev/docs/ai/core-concepts/output/

## 技术栈候选

### Python-first Agent Core

- Core: Python package with Pydantic v2 models and stable schemas。
- Kernel: handwritten PatternRunner, CapabilityRegistry, SessionCoordinator, AgentEngine protocol。
- Runtime: LangGraph adapter after direct deterministic runner。
- LLM: PydanticAI or lightweight Pydantic-based provider adapter behind LinguaLoop boundary。
- Testing: pytest, provider mocks, deterministic Pattern fixtures。

适合手写核心、保持领域语义清晰，并避免重写完整 agent harness。

### Web-first TypeScript

- Frontend: Next.js 或 Vite + React
- Backend: Node.js API、Next.js route handlers，或轻量独立服务
- Storage: SQLite/Postgres 起步
- LLM: provider adapter 封装 OpenAI-compatible API

只适合作为前端候选；不再作为核心 agent 层的默认方向。

### Local-first Desktop / PWA

- Frontend: React + local persistence
- Storage: IndexedDB 或 SQLite wrapper
- Sync: 后续再做可选云同步

适合强调用户数据可控，但早期工程复杂度更高。

### Three-layer Extension Core

- Core: TypeScript domain package with stable schemas。
- Runtime: lightweight plugin manifest, capability registry, lifecycle hooks。
- Plugins: first-party packages for providers, voice, avatar, importers。
- Patterns: first-party or third-party learning flows with explicit capability requirements。
- Voice: `voice-livekit` as a first-party plugin candidate, not a core dependency。

适合在不牺牲学习闭环一致性的前提下扩展多模态能力。

## 待决策项

- 开源许可证：MIT、Apache-2.0、AGPL-3.0 或其他。
- 第一版部署目标：本地开发优先、云端 demo，还是可自托管。
- LLM provider 策略：单 provider 起步，还是从第一版就做 provider registry。
- 鉴权策略：无登录本地版、邮箱登录，还是第三方 OAuth。
- 插件 manifest 格式、权限模型、版本兼容策略。
- Pattern manifest 格式、capability requirements、fallback 策略。
- 第一批官方学习 Pattern 清单。
- Decision 0004 何时从 Proposed 升级为 Accepted。
