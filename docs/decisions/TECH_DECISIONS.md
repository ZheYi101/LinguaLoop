# Technical Decisions

## Decision 0015: 同库准备缓存、可选历史与实机验收

- Status: Accepted
- Date: 2026-10-28

用户要求打开正常软件就能看到小说预处理和实际对话历史。继续使用标准库 SQLite，将准备缓存和业务资料放在默认应用数据库；启用 WAL、按操作连接/事务和材料会话索引，不增加缓存服务。缓存键按内容哈希、标题、语言/profile、推理服务/模型和准备版本隔离，排除 API Key，支持密钥轮换；`analysis_cache_key=None` 兼容旧记录。相同导入复用材料 ID，部分缓存等待显式继续，完整缓存不能被部分进度覆盖。

对话页提供按材料的历史选择，恢复旧线程不改变排序，完成线程只读，启动恢复最近会话。缺少有效配置时打开本地库，但在线操作明确失败，禁止自动生成 mock 回答。未发送草稿只在内存保留；材料、准备资料及确认消息本地持久化。

当前采用正常 Windows 应用目录。已有真实 Pro 准备可迁入同版本缓存，但小说必须通过实际窗口导入；实际对话必须通过控件输入/发送，不能用 fixture 填充用户历史。探针以 Qt 鼠标/键盘事件驱动可见 Windows 窗口，分别测量模型首字/完整耗时、UI 首文本/后续帧和发送至操作结束。缓存命中不能替代真实讨论质量。

整书汇总在实际调用中曾耗时超过 5 分钟，新增独立 `OPENAI_SYNTHESIS_DEADLINE_SECONDS=600`；一般非流式调用仍默认 240 秒，后台受 45 秒外层预算约束。这只允许长任务完成，不是对话延迟优化。数据库和相邻 WAL 文件含敏感材料/历史，均从 Git 忽略，备份先关闭应用。整书汇总成功、真实 Flash 历史及舒适性仍待服务可用后验证。

## Decision 0014: 以完整真实小说验证两层材料准备和读者式对话

日期：2026-10-28。用户提供完整《Lolita》EPUB，要求实际预处理后连续对话，并评价响应速度及读者体验；停止 orchestrator 与子 agent 工作方式，由主助手直接实现和验收。

原逐段拼接概要和首 300 字符实时摘要无法贯通长篇；8000 token 的 Pro 小任务在真实调用中多次 `finish_reason=length`，相同预算的重试仍截断。因此保留全书分段和逐段落盘，增加整书 Pro 汇总；段落采用更精简的两题结构、low/16000 输出预算，若明确截断只再以 24000 重试一次；普通结构错误仍至多两次。思考预算与最终 JSON 共享上限，不关闭推理模型的思考来冒充通过。默认最多并发 3 段，可配置 1–4；默认材料上限 1000000 字符，长篇段落最多 24000 字符。整书汇总原 high/24000 在真实调用中两次截断，改为精简重复笔记字段、Pro low/24000，明确截断时仅以 32000 再试一次；成功前禁止开聊。

新增 `MaterialAnalysis.overview_complete=False` 兼容旧数据；同边界和哈希的段落复用稳定 ID，全文未变且汇总完成才复用整书结果。失败、超时或取消保留已保存段落，取消其他请求；供应商已经接受的请求计费情况不能由本地取消推断。

快速模型只拿保存的准备资料：当前题、完整的简短整书概要、按本轮发言挑选的情节/人物、最近十条消息与少量早期读者观点。当前发言及改口优先于预测；后台参考也随实际话题变动。没有引入向量服务、额外模型或全文实时推理依赖。代价是词匹配仍可能漏掉隐含关联，需通过实际对话识别并迭代，而不是用引用存在性自动判定语义正确。

验收使用真实配置、完整 EPUB、持久化数据库及连续应用进程中的多轮交谈，分别计首字、完整模型回复和应用端到端时间；1 秒保留为优化目标。评价涵盖具体事实、人物动机、叙述可靠性、追问、分歧、改口、自然收束及重启恢复。质量不能由非空输出或结构通过代替。原文与会话只存本地忽略目录，提交文档只记录必要事实、问题和元数据。

本文档记录会影响长期维护的产品与技术选择。已接受的后续决策覆盖早期记录中的对应范围；当前产品主旨见 [Project Brief](../product/PROJECT_BRIEF.md)。Decision 0010 调整语音优先级与 MVP 边界，早期“文本 MVP 先行、语音后续增强”的表述仅保留为历史背景。

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

## Decision 0009: 本地 SQLite 持久化和主动结束复盘进入 MVP

- Status: Accepted
- Date: 2026-09-09

### 背景

桌面端 POC 已经能通过内存态完成材料分析、练习对话和导出，但用户关闭或重启软件后无法继续看到材料、会话和复习项。当前产品目标强调真实材料、用户输出证据、反馈来源和 review queue 的连续性，因此内存态无法支撑 MVP 验收。

同时，外部产品调研显示，材料导入、AI 解释和卡片生成已经是常见基线。LinguaLoop 的差异应落在可追溯学习证据链，而不是只做更多格式的导入或泛用聊天。

### 决策

- MVP 运行时持久化采用本地 SQLite，使用标准库 `sqlite3`，暂不引入 ORM。
- 默认数据库路径为平台应用数据目录下的 `LinguaLoop/lingualoop.sqlite3`，允许用 `LINGUALOOP_DATA_DIR` 覆盖。
- 存储材料、会话、消息、反馈、复盘、review items、review outcomes 和 `SessionEvent`。
- Markdown 和 DOCX 是第一批文件导入格式；旧式 `.doc`、PDF、视频和 Google Docs 在线授权暂不进入第一阶段。
- 多轮练习过程中只生成即时反馈；最终 review candidates 在用户点击“结束并复盘”后集中生成。
- 桌面端采用左导航、中工作区、右上下文的工作台布局，并在窄屏下折叠。

### 影响

- `LearningWorkbench` 成为本地恢复、材料列表、会话完成和 review queue 的应用层边界。
- Provider contract 增加 `summarize_session`，用于输出结构化 `SessionReview`。
- `ReviewItem` 需要保存来源材料、来源会话、状态和 `due_at`，`ReviewOutcome` 记录 `again/hard/good/easy`，控制事件覆盖 pause、ignore、archive、delete 和 mastered。
- JSON 导出继续作为备份和迁移出口，但不承担运行时状态。
- Mock provider 继续用于 CLI、测试和显式离线调试；普通桌面模式不自动降级到 mock。

### 未解决问题

- SQLite 当前使用 JSON payload table，后续需要评估何时拆成更细粒度 repository schema。
- `LearningSegment` 已进入 Core，但 segment 自动切分和来源位置标注还需要继续补强。
- 基础 due date 调度已经可用，但完整 spaced repetition 算法仍留到后续阶段。

## Decision 0010: 沉浸语境驱动语音输出成为产品主线

- Status: Accepted
- Date: 2026-10-24
- Supersedes: Decision 0002、0003 中语音仅为后续增强、不进入 MVP 关键路径的范围安排；保留其 Core / Plugin / Pattern 与可替换语音实现边界。

### 背景

用户明确提出将既有语境练习与沉浸式学习结合：继续按兴趣看番、看视频等，把已经接触过的内容作为语境，让 AI 先理解材料、总结可聊内容、推荐话题，主要通过语音对话练输出；愿意时也可以玩语境 roleplay。

现有文本对话、材料分析和复习队列可以复用，但“把字幕变成课程”和“把语音放到远期插件阶段”不能完整表达本次主旨。用户也保留了按自己认可的学习理论调整练习的长期方向。

### 决策

- 产品主旨确定为“沉浸提供语境，LinguaLoop 帮你练输出”，语音对话是核心体验。
- 默认入口是材料理解后的话题推荐与自然讨论；roleplay 自愿，词汇讲解和理解测验不作为开聊前提。
- 正式 MVP 必须包含基础多轮语音输入和 AI 语音回复。现有文本闭环定义为原型基础，并保留为辅助和故障回退。
- 语音通过可替换 provider / plugin capability 接入，不因此把具体 SDK 放进 Core；本次不重新选择 SDK、引入外部服务或修改实现。
- 方法可配置保留为产品方向，MVP 先支持基础练习偏好；完整自定义理论编辑器、连续实时双向语音和 avatar 留在后续范围。
- 继续保留真实输出证据、可追溯反馈、主动结束复盘和本地 review queue；不把话题生成或内容展示计为掌握。

### 影响

- `PROJECT_BRIEF.md` 成为当前主旨的权威入口；README、AGENTS、MVP、路线图和相关架构文档同步对齐。
- 路线图新增核心语音 MVP 阶段，先补齐话题选择、自然讨论和基础语音，再扩展实时交互与更多学习方法。
- Plugin 在实现上可替换，不意味着语音在产品验收上可省略；文字回退不能代替语音验收。
- 当前代码中的文本流程保持可用；本次是文档与范围更新，不宣称话题、语音或方法配置已交付。

### 未解决问题

- 基础语音 provider、轮流说话的具体交互方式、延迟和成本是否满足实际使用。
- 话题质量、材料范围和来源关联的最小结构，以及字幕导入增强的具体设计。
- 学习理论配置如何落到可测试、可复盘的 Pattern 参数或扩展，而非任意 prompt。
- 新主线是否能帮助用户更愿意开口和持续输出，需要真实使用验证。

## Decision 0011: MD3 桌面与独立分轮语音实现

- Status: Accepted
- Date: 2026-10-24
- Supersedes: 早期 Windows 默认 Kirigami 壳、固定三栏布局与逐轮强制纠错；保留 Python-first、provider 可替换和 SQLite 的既有选择。

### 背景

用户批准以 MD3 统一首版 UI，并交付“材料 → 话题 → 分轮语音 → 轻量复盘”。现有 UI 组件层级不统一、侧栏压缩对话，SQLite 共享连接跨线程报错，每次请求创建独立 asyncio loop 也不适合复用网络 client。

### 选择

- Python ≥3.11、Pydantic 2、PySide6 6.11.1/QML，Windows 默认 ApplicationWindow；Kirigami 仅显式启用。加载 QML 前统一 Qt Material 样式。
- `AppTheme` 和项目组件管理 MD3 语义色彩、字体、形状与状态，紫色种子 #6750A4，系统/浅/深主题和减少动效保存在 QSettings。
- <600 使用底部导航，600–1199 使用 80px rail，≥1200 对话页增加 320px 语境面板。
- 增加 pysubs2 1.8.x 解析 SRT/VTT；保留原文和 cue 起止时间，topic 引用必须在规范化材料中出现。单次分析限制 30000 字符，长材料保存后提示选片段，不静默截断。
- 明确 `DiscussionTopic` 与 `PracticeOptions`；默认自然讨论、低强度和结束反馈。纠错失败不阻断对话，反馈和复习证据不足可为空，单次复盘最多三个重点和三个复习项。
- 语音采用 Qt Multimedia WAV + 独立 STT/TTS protocol 和 httpx adapter，配置使用 `LINGUALOOP_STT_*` / `LINGUALOOP_TTS_*`。文本服务不自动继承为语音服务。
- 最多录音 60 秒，识别后由用户编辑确认，再发送生成和合成；合成重试不重新调用文本模型。
- SQLite 按操作连接与事务，后台采用一个长期运行 asyncio worker；音频和 GUI 留在主线程，正常退出关闭任务与临时文件。
- 编排继续 deterministic runner，不增加新数据库、云编排或大型 UI 框架。

### 影响

Core 与供应商/Qt 保持隔离，QML 拆成设计系统、组件和业务页面；新增资源通过 package-data 随 wheel 分发并验证。旧 payload 通过默认值读取；旧会话保留兼容语义。材料里的指令作为内容处理，云端音频与确认后的本地文本分开保存。

### 未解决问题

- 真实服务、麦克风、播放、延迟和成本仍需至少三轮真人验收，mock 结果不能替代。
- 当前只构建 Python wheel；独立 Windows 安装器、代码签名和 Qt runtime 打包尚未交付。
- 强制终止可能留下系统临时目录，后续可增加启动时清理策略；不存原始音频供重启恢复。
- 完整理论编辑器、连续通话/自动打断、材料原地管理、跨整季索引和移动端继续留待后续。

## Decision 0012: DeepSeek 双角色、可接续材料准备与文本优先验收

- Status: Accepted
- Date: 2026-10-24
- Supersedes: Decision 0011 的单次 30000 字符限制、固定少量话题以及本阶段依赖 STT/TTS 验收的先后顺序；产品仍以沉浸语境下的自然输出为目标。

### 背景

用户要求围绕材料和对话，先用现有 DeepSeek 配置完成纯文本测试；材料包含整本小说、Excel、EPUB 或带字幕的视频。推理模型应提前准备丰富话题和常见回答，在对话后台按需继续准备，前台短回复由 Flash 执行，以完整回复低于 1 秒为性能目标。文本验证后再转向 LiveKit 连续语音。

### 选择

- 复用 Python core、deterministic runner、SQLite 和 provider 抽象，不新增数据库或云索引。Excel 增加必要的 openpyxl；EPUB 用标准库读取 spine 和 HTML 文字。视频当前只读取同名字幕，未调用视觉模型。
- 首选 `deepseek-v4-pro` 思考模式负责整理与后台准备，`deepseek-flash` 非思考模式负责所有前台轮次。显式分别发送 thinking 参数，推理角色加 high effort；旧 `OPENAI_DISABLE_THINKING` 不再覆盖推理。依据 [DeepSeek 模型表](https://api-docs.deepseek.com/quick_start/pricing/) 与 [思考模式说明](https://api-docs.deepseek.com/guides/thinking_mode/)。
- 原文先保存；按最多 12000 字符处理，逐块持久化哈希、摘要、规范化结果和证据。失败可恢复已完成块。默认 360000 字符安全预算显式可配置到 5000000，超限提示分卷，不静默截掉章节。
- 材料保存大纲、人物、块摘要与最多 60 个跨章话题；每题可保存多个候选用户意图、短回复要点及精确引用。自定义话题在开聊前推理准备并保存。
- 前台仅用话题准备包、已完成后台准备和近期六条消息流式回复；背景候选不是用户事实。用户每条消息限制 4000 字符。回复失败不将半消息持久化。
- 背景最多 12 次/会话、45 秒/次、一个并发，采用 revision/代际/会话标识验证；新发言、换材料、结束和重置取消旧请求。异常或过期结果不阻塞当前轮。
- 新生成结果严格校验：后台意图、要点、精确引用均非空；材料与自定义话题必须有完整的有来源回答分支。部分无效分支剔除；缺失/全空/全无效时最多两个格式尝试，后台 45 秒覆盖整个准备任务。失败保留旧有效 snapshot 但不标 ready。旧数据的默认空字段仍允许读取。
- 审查补充：消费旧 snapshot 前也执行严格校验，允许读取历史不表示可将无引用内容交给 Flash。话题预算跨所有章节轮询；自定义题按全部块与原文的轻量相关性挑选、附命中窗口和全书分布概览，保留明确来源范围。
- 真实首轮计时显示完整回复 1 秒尚未普遍达成；可逆优化只去重重复证据、当前发言及无用 UUID，保留分支与回答质量、160-token 输出预算。Pro 后台小任务最终采用 low effort、4000-token 上限；历史 low/2500 两次未 ready 的测量保留，分析继续 high。实测单次分析输出 19231 tokens，因此分析上限设为 24000；每次非流式模型默认 240 秒 wall deadline、全材料单次运行默认 1800 秒总预算，超时后可从保存块接续。对应配置见 `.env.example`，增加预算将增加成本。
- `ChatOpenAI` 会将 `max_tokens` 改写为 OpenAI 字段 `max_completion_tokens`。DeepSeek 使用同库 `BaseChatOpenAI` 保留官方字段，透过 MockTransport 断言实际 wire JSON 参数，而不只断言 Python settings；泛 OpenAI 仍保留原客户端。
- 最后一次有界后台修复：low/2500 的两次真实输出都恰好 2500，但当时缺少 finish_reason，不能据此直接断言截断。新增仅含安全元数据的诊断，后台输入仅当前题与两轮、少量备选和单引文；输出缩成一意图、一两个短要点和一引文。独立后台预算调整为 low/4000，仍为思考角色、单并发、45 秒总任务、12 任务/会话。明确 length 时不做同预算重试，其他结构无效仍最多两次；不 fake ready，也不将预测计入用户历史。最终微型包 low/4000 已真实验证一次 10.69 秒 ready，随后 included 到唯一 Flash 请求；没有意图准确率标注或提速因果证据，不能从单例推导稳定性，见[文本独立验收](../planning/TEXT_ACCEPTANCE_2026-10-24.md)。
- 首个内容块 TTFT 与完整模型耗时分别测量，端到端耗时另测。不能从 TTFT 低于 1 秒推导完整回复达标。
- 新讨论即时纠错延后到结束（包括历史 immediate 偏好），确保 Pro 不进入前台路径；直接 runner 的旧 options=None 保持兼容。

### 影响和未解决问题

旧业务 JSON 通过默认空列表、空 preparation 和完成标记兼容读取。真实材料仍会上传配置的模型服务，按敏感数据处理；不记录原始推理链、密钥或完整模型日志。长材料整理会产生多次 Pro 调用，增加预算前应考虑成本。精确引用只能证明来源存在，不能自动证明所有 AI 解释正确，仍需真实素材质量验收。完整回复低于 1 秒是待测目标，网络和模型服务时间可能无法满足；不得因流式 UI 可用就宣布达成。LiveKit 及 STT/TTS 选择由后续文本验收门决定。

## Decision 0013: 以可选 Python RTC adapter 做严格 loopback 探针

- Status: Accepted（技术探针边界；真实 RTC 连通未通过）
- Date: 2026-10-24

### 背景

文本功能和真实前台调用已验证，完整回复 1 秒尚未稳定达到；用户明确选择保留该优化目标，先做 LiveKit 探针。此时需要验证 transport、连续 PCM、文本流和取消生命周期，而不提前实现整套云语音 UI 或引入模型框架。

### 决策

- 新增独立 `lingualoop.realtime`；协议、PCM 与接收代际 gate 不依赖 SDK。仅 `realtime` extra 安装固定版 `livekit` / `livekit-api`，不引入 `livekit-agents`。业务和 LLM provider 不依赖 RTC；transport 不修改 `DialoguePreparation`。
- 可靠文本事件带 session/turn/generation/seq，draft 仅在显式 done 后完成。generation 绑定一条连续 PCM 轨和 SID；取消立即关闭接收呈现门、清发送队列、释放旧轨，旧代际不能冒充新轮。
- 使用可校验的官方 Windows server 资产，缓存于 ignored build；不创建云账号、服务、公网入口、firewall 规则或全局安装。HTTP/UDP 实际 socket 必须严格 loopback。当前官方 server 的 RTC TCP listener 无独立 bind IP 配置，故禁用 TCP fallback，不能以 `--bind` 或 node_ip 广告代替 socket 检查。
- SDK 的空 ICE 列表会继承 server ICE 表；初版误用非空、空 URL 的 ICE entry，违反 libwebrtc 校验，是探针配置缺陷。修正为由探针显式传入合法 `stun:127.0.0.1:<已审计UDP端口>`，非空 URL 阻断回退；不新增 STUN 服务或监听。探针严格校验 literal loopback、canonical URL 和精确端口，adapter 通过显式配置接收，不把本机限制加入 core。RTC exercise 在隐藏短命子进程内运行，父进程硬截止和 PID/socket 检查覆盖 native 握手超时；临时密钥不进命令行/结果/仓库。

### 影响和未解决问题

当前离线协议/清理测试通过，Windows server 的 loopback 监听及退出可复核。历史空 ICE 列表出现真实握手 timeout，但有继承默认 ICE 的限制；随后空 URL entry 的独立 ConnectError 来自无效配置候选，不能证明本机 loopback 不可用。合法本机 URL 修复经离线自验和唯一一次独立差异 RTC 复验：首 client 连接约 44.9 秒后被总 deadline 取消，`operation_deadline`、native 创建 `not_observed`，不能推断已进入 ICE 握手；所有自有进程/socket 清理通过。双参与者 PCM/文本/取消/重入尚未到达，不记通过。不因此放宽网络范围或增加云服务。现有 QML 和分轮语音继续使用原实现，未接新 adapter。完整 VAD/AEC、STT/TTS、播放队列打断、真人语音、自动断网恢复与设备切换均待后续验证。具体版本、限制、命令和失败证据见 [LIVEKIT.md](../desktop/LIVEKIT.md)。
