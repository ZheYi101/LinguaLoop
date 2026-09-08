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
- 后续脚手架应以 `docs/product/MVP_SPEC.md` 和 `docs/architecture/ARCHITECTURE.md` 为事实来源。
- 技术栈选择需要在本文档中补充新的 decision entry。

## Decision 0002: 采用 Core / Plugins / Patterns 三层扩展架构

- Status: Accepted
- Date: 2026-08-25

### 背景

项目希望支持语音、Live2D、不同学习 pattern、复习调度、材料导入、LLM/STT/TTS provider 等能力扩展。通用 agent harness 展示了 capability registry、plugin registry、event log 和 runtime adapter 等可借鉴的工程结构。

LinguaLoop 可以借鉴这种插件组合思想，但产品目标不同。LinguaLoop 的核心价值来自稳定学习闭环，而不是任意 agent 能力组合。学习 Pattern 也不应被混同为普通能力插件：Pattern 负责「怎么学」，Plugin 负责「能做什么」。

### 决策

LinguaLoop 采用 `fixed learning core + optional plugins + capability-aware patterns`。

- Core 定义学习材料、练习会话、消息、反馈、复习项、session events、Pattern contract、capability contract 和结构化输出。
- Plugins 是可用可不用的能力提供者，例如语音、Live2D、材料导入、LLM/STT/TTS provider。
- Patterns 是可组合的学习流程，例如 roleplay、shadowing、retell、spaced-review。Pattern 可以依赖特定 capability，但不直接依赖具体插件实现。

插件通过明确 contract 扩展能力，不能直接改写 core schema 或绕过学习状态机。Pattern 通过 capability requirements 声明运行条件。

Codex、Claude Code、DeepSeek Harness 等通用 agent 系统可以作为结构参考，但不作为 LinguaLoop 的总基座，也不定义 LinguaLoop 的学习流程。

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

项目主语言倾向 Python。核心 agent 层需要支持 Pattern 执行、插件能力调用、结构化输出、可恢复会话、事件记录和后续语音扩展。

LinguaLoop 的 agent 定位不是通用任务 agent。它不需要像 Codex 或 Claude Code 那样理解和解决任意开放目标；它需要围绕用户输入材料执行稳定的 language learning loop：输入理解、任务化对话、即时纠错、复述输出和间隔复习。

因此项目可以手写自己的领域化 agent kernel。复杂度应集中在学习语义、Pattern contract、事件记录和 provider 边界，而不是构建一个自由规划的完整 agent harness。

### 决策

采用 Python-first 核心架构：

- Core 使用 Pydantic models 定义领域对象、事件、Pattern contract 和 capability contract。
- Agent Kernel 手写 `PatternRunner`、`CapabilityRegistry`、`SessionCoordinator`、`AgentEngine` protocol 和 `EventStore` interface，定位为领域学习流程执行器。
- 系统灵活度主要放在 Pattern 层；Pattern 决定练习模式、语境、纠错强度、输入 modality、结束条件、复习项生成和复习节奏。
- 默认 `AgentEngine` adapter 使用 LangGraph，负责 stateful workflow、routing、streaming、checkpoint / resume。
- typed LLM calls 使用 PydanticAI 或轻量 Pydantic provider adapter，统一包在 LinguaLoop 的 `TypedLLMClient` 后面。
- LiveKit 继续作为 `voice-livekit` 插件的 SDK，不进入 Core 或 Agent Kernel。

### 影响

- 不采用 DeepSeek Harness 作为主 runtime，但保留实验性 adapter 的可能。
- 不引入通用自由规划 agent loop；LLM 生成具体语言内容，但不拥有学习流程控制权。
- 第一阶段先实现 direct deterministic runner，确保手写核心可理解、可测试；LangGraph adapter 在同一 flow 稳定后接入。
- Core 和 Kernel 不直接暴露 LangGraph checkpoint、PydanticAI agent 或 LiveKit room 概念。
- 项目默认语言约定从 TypeScript-first 调整为 Python-first core；前端可独立选择 TypeScript / Web 技术栈。
- 初始 Python package scaffold 已创建，LangGraph 先作为 `engine.langgraph` adapter 引入，core 只保留领域模型和 provider contract。

### 参考

- LangGraph overview: https://docs.langchain.com/oss/python/langgraph/overview
- LangGraph graph API: https://docs.langchain.com/oss/python/langgraph/graph-api
- PydanticAI agents: https://pydantic.dev/docs/ai/core-concepts/agent/
- PydanticAI output validation: https://pydantic.dev/docs/ai/core-concepts/output/

## Decision 0005: 以真实输入和输出证据定义学习闭环

- Status: Accepted
- Date: 2026-08-28

### 背景

LinguaLoop 的思考起源来自一个已实际使用的 `input-driven-language-coach` skill 和 EnglishLearningWorkflow 经验工作区。该工作区包含 raw/cleaned/segments/lessons/sessions 的材料流、输入驱动 lesson、summary-first review，以及独立的 CORA spoken-retrieval practice。

这些实践显示，产品价值不在“一次性生成解释”，而在把真实输入材料转化为可输出、可纠错、可复习、可延迟检索的学习证据链。外部学习科学也支持类似方向：noticing、output、retrieval practice、distributed practice 和 formulaic language 都提示系统应促成注意、输出、回忆、间隔和语块完整性，而不是只提供被动讲解。

### 决策

LinguaLoop 的 MVP 和后续架构采用以下学习闭环作为产品约束：

```text
真实输入 -> 语境理解 -> 高价值目标选择 -> 检索/输出 -> 纠错 -> 复习项 -> 延迟再输出
```

具体约束：

- 用户材料必须保留 raw、normalized/lesson-ready、segment 的概念边界。
- `track` 是显式业务属性；`live_chat`、`article_reading`、后续 `spoken_retrieval` 等 track 可共享对象，但不能被文件后缀替代。
- 用户真实输出、冷启动尝试、复习结果和延迟检索结果才是学习状态更新证据。
- `FeedbackItem` 应优先表达 pattern-level 问题，并能关联到用户消息或材料片段。
- `ReviewItem` 应是可重新检索或迁移使用的任务，不只是词条收藏。
- Profile Delta 是当前证据快照，长期 profile 应从事件、反馈和复习结果重建。
- CORA spoken-retrieval 与 input-driven lesson 是不同 Pattern 家族，不能强行合并成一个六段 lesson 模板。

### 影响

- Product spec 需要把主动输出、反馈证据、review candidates 和 summary-first review 作为 MVP 验收约束。
- Architecture 需要明确 material lifecycle、session events、learner profile snapshot 和 review queue 的边界。
- Pattern contract 需要允许不同学习方法拥有不同状态机，同时共享 `PracticePlan`、`SessionEvent`、`FeedbackItem` 和 `ReviewItem` 等 core 对象。
- Provider adapter 不能只提供 free-form chat completion；它需要支持结构化材料分析、纠错、复习项生成和 profile delta 生成。
- 不应把生成 lesson、展示 model answer 或展示复习项计为掌握；只有后续输出证据能更新学习状态。

### 未解决问题

- MVP 是否纳入 `spoken_retrieval` / CORA 作为正式 Pattern，还是先作为 roadmap 中的后续 Pattern。
- `LearningSegment`、`ProfileDelta`、`ReviewOutcome` 和用户控制事件的最终 schema。
- Review 调度第一版使用简单 due date，还是引入更完整的 SRS 参数。
- 如何在公开 demo 中展示经验样本价值，同时不暴露个人学习材料和历史。

### 参考

- Learning Loop Foundation: ../research/LEARNING_LOOP_FOUNDATION.md
- Practice Workspace Findings: ../research/PRACTICE_WORKSPACE_FINDINGS.md
- Schmidt 1990, noticing hypothesis: https://doi.org/10.1093/applin/11.2.129
- Swain 1998, output hypothesis: https://doi.org/10.1016/S0346-251X(98)00002-5
- Karpicke & Blunt 2011, retrieval practice: https://doi.org/10.1126/science.1199327
- Cepeda et al. 2006, distributed practice: https://doi.org/10.1037/0033-2909.132.3.354
- Wood 2006, formulaic language in L2 speech: https://eric.ed.gov/?id=EJ750535

## Decision 0006: 先做 CLI POC，再做 Python-native 桌面壳

- Status: Accepted
- Date: 2026-09-07

### 背景

当前核心闭环已经能在测试中跑通，但还没有稳定的用户壳。为了尽快验证真实材料导入、分析、对话、纠错、复盘和导出这条链路，先需要一个最小可运行的命令行原型。

### 决策

- 先实现无 UI CLI POC，作为第一条可操作入口。
- CLI 通过共享的 application service 调用 kernel / provider，不直接绑定 LangGraph 或具体 LLM SDK。
- 下一阶段桌面端优先采用 Python-native 壳，复用同一套 application service；WebUI 不作为主线。

### 影响

- CLI 可以直接用于本地 smoke test 和功能验收。
- 桌面端与 CLI 共用同一业务服务层，后续更容易替换交互外壳。
- WebUI 仍可保留为未来可选项，但不会先成为主交互。

## Decision 0007: 桌面端采用 PyQt6 + PyQt-SiliconUI POC（Superseded）

- Status: Accepted
- Date: 2026-09-08

### 背景

项目已经有可运行的 CLI POC 和共享 application service。下一步需要验证本地桌面端交互壳，并且用户偏好 PyQt-SiliconUI 的视觉风格。已检查 `feature/pyqt6-migration` 分支：该分支描述中提到 PySide6，但实际依赖和源码 import 均以 PyQt6 为主，因此当前不能按 PySide6/QML 直接使用。

### 决策

- 桌面端 POC 改为 `PyQt6 + PyQt-SiliconUI`。
- `PyQt-SiliconUI` 通过 Git 依赖接入 `feature/pyqt6-migration` 分支，不 vendor 第三方源码，也不使用 submodule。
- 桌面端先作为薄 UI 壳复用 `LearningWorkbench`，不直接依赖 LangGraph、ChatOpenAI 或 provider 内部。
- 默认使用真实 OpenAI-compatible provider，通过 `OPENAI_*` 环境变量配置；mock provider 仅通过显式参数用于离线调试。

### 影响

- 项目会受到 PyQt-SiliconUI GPLv3 许可证影响；如果未来希望改用 MIT、Apache-2.0 或闭源分发，需要重新评估 UI 依赖或移除该组件库。
- Git 分支依赖的稳定性弱于正式发布包；后续需要关注上游迁移进度，并在需要时固定 commit 或替换组件库。
- 第一版桌面端使用中文浅色界面，只验证窗口启动和最小学习闭环，不承诺完整 UI 体验、持久化或真实 API 异步调用体验。

## Decision 0008: 统一采用 PySide6/QML + Qt Quick Controls 6 + Kirigami

- Status: Accepted
- Date: 2026-09-08
- Supersedes: Decision 0007

### 背景

LinguaLoop 后续需要同时覆盖桌面端和移动端。语言学习在手机上不是桌面三栏布局的简单缩小，而是材料、练习、输出、反馈、复盘的连续任务流。QML 更适合快速调整响应式布局和触控交互，Kirigami 针对桌面与移动设备的 convergent application 场景设计。

### 决策

- UI 主线采用 `PySide6 + QML + Qt Quick Controls 6 + KDE Kirigami`。
- Kirigami 作为桌面端和 Android 端的应用壳，核心页面共享 QML 实现。
- QML 只调用 Python `QObject` ViewModel 的 properties、signals 和 slots；不直接调用 LangGraph、ChatOpenAI、provider 或 Pydantic 内部对象。
- `LearningWorkbench` 继续作为应用层边界，Core、Kernel 和 Provider 保持 Python-first 且与 UI 框架无关。
- LLM 操作放入 Python worker/thread，界面只处理 loading、结果和错误；请求失败时保留用户当前输入。
- Android 优先进行移动端运行验证，iOS 暂不作为第一阶段目标。
- Decision 0007 的 PyQt6 与 PyQt-SiliconUI 路线不再作为主线，相关依赖移除。

### 影响

- PySide6 通过 Python 依赖安装；Kirigami 是 Qt QML runtime，不把 PyPI 上同名的 `kirigami` 包视为 KDE Kirigami 依赖。
- Windows、Linux 和 Android 需要分别验证 QML module 发现、运行时分发和打包方式。
- Windows 开发期不得把 Craft 编译的 Kirigami native plugin 直接注入 PyPI PySide6 的 Qt 进程。检测到这种组合时，应用自动使用 Qt Quick Controls fallback；正式 Kirigami Windows 分发必须使用同源的 Qt、PySide6 和 Kirigami runtime，并在独立打包 spike 中验证。
- Kirigami/Qt 依赖的 LGPL/GPL 组合、图标资源和平台打包方式需要在发布前单独审查。
- 首版页面采用材料、练习、复盘导航；移动端优先保持单列、可返回、可滚动和适合触控的交互。

### 参考

- Qt Quick Controls: https://doc.qt.io/qt-6/qtquickcontrols-index.html
- Kirigami Getting Started: https://develop.kde.org/docs/getting-started/kirigami/
- Kirigami Python Setup: https://develop.kde.org/docs/getting-started/kirigami/setup-python/
- Kirigami Windows Setup: https://develop.kde.org/docs/getting-started/kirigami/platforms-windows/

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
