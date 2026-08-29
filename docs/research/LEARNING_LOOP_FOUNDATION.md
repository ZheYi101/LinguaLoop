# Learning Loop Foundation

本文档沉淀 LinguaLoop 第一版学习闭环的理论基础和实践约束。它不是文献综述，也不宣称某一种学习法被证明为唯一最优；它的作用是把项目已有理念、`input-driven-language-coach` skill、EnglishLearningWorkflow 实践样本和少量学习科学依据合并成可执行的产品原则。

## 结论摘要

LinguaLoop 应被设计成一个围绕真实输入材料运行的学习循环系统，而不是泛用聊天机器人、单词本或一次性 lesson 生成器。

核心闭环应固定为：

```text
真实输入 -> 语境理解 -> 高价值目标选择 -> 检索/输出 -> 纠错 -> 复习项 -> 延迟再输出
```

这条闭环的关键不是让 AI 一次性解释更多内容，而是让学习者在真实语境中暴露可观察表现，再把表现转化为下一轮练习证据。

## 证据来源

### 项目内来源

- LinguaLoop 当前 `docs/product` 和 `docs/architecture` 文档。
- 本地 `input-driven-language-coach` skill：作为项目思考起源，提供了输入合同、清洗、分轨、课程结构、profile delta、review policy 和 workspace schema。
- EnglishLearningWorkflow 经验工作区：作为实践样本，只读参考其材料、segments、lessons、sessions、review 和 CORA spoken-retrieval 记录；本文不记录个人绝对路径，也不复制完整学习答案。

### 外部理论锚点

- Richard Schmidt 的 noticing hypothesis 强调学习者对输入中特征的意识/注意问题，适合支撑 LinguaLoop 的“理解检查 + 对比纠错”设计。参考：`The Role of Consciousness in Second Language Learning`，Applied Linguistics, 1990, DOI: https://doi.org/10.1093/applin/11.2.129。
- Merrill Swain 的 output hypothesis 强调输出不只是学习结果，在一定条件下也能促使学习者发现表达缺口、测试语言假设并获得反馈。参考：`Comprehensible output?`，System, 1998, DOI: https://doi.org/10.1016/S0346-251X(98)00002-5。
- Retrieval practice 研究支持把“回忆/再生成”作为学习活动，而不是只重读材料。参考：Karpicke & Blunt, 2011, DOI: https://doi.org/10.1126/science.1199327；Dunlosky et al., 2013, DOI: https://doi.org/10.1177/1529100612453266。
- Distributed practice / spacing 研究支持把复习接口留在产品闭环中，即使 MVP 暂不实现完整 SRS。参考：Cepeda et al., 2006, DOI: https://doi.org/10.1037/0033-2909.132.3.354。
- Formulaic language 研究提醒口语流利度不能只拆成孤立单词，尤其是 live-chat / spoken retrieval 场景。参考：Wood, 2006, ERIC: https://eric.ed.gov/?id=EJ750535。
- Intelligent Tutoring Systems 的常见分层可以作为结构类比：domain model、student/learner model、tutoring model、interface model。LinguaLoop 不需要复制传统 ITS，但这种分层支持把“材料/语言知识、学习者状态、教学决策、交互界面”分开建模。参考：Ryan Baker, `Intelligent Tutoring Systems`, https://learninganalytics.upenn.edu/ryanbaker/ITS2020/topical-wk-1/its-7.html。

## 理论到产品原则

### 1. Noticing: 不能只输入，要制造可见差距

如果用户只是看过一段材料，系统无法知道哪些语言点真的被注意到。LinguaLoop 需要用理解检查、错误高发改写和源句对齐，让学习者看见“我以为懂了”和“我能准确使用”之间的差距。

产品含义：

- Material analysis 不能只输出摘要，还要输出可练习的表达、难点和可检查目标。
- Feedback 需要指向具体源句、用户句子或语境，不应停留在泛泛语法建议。
- `FeedbackItem` 应记录 `original`、`corrected`、`explanation` 和来源 message/segment。

### 2. Output: 用户输出是学习证据，不只是交互内容

输出任务能暴露理解输入时看不出来的问题：语块断裂、搭配不稳、时态链混乱、句子开头迟疑、寄托在中文结构上的直译等。

产品含义：

- 会话中的用户消息应被当作 evidence，而不是只作为下一轮 LLM 上下文。
- Profile 更新必须来自真实回答、冷启动输出、复习结果或延迟检索，不应因为系统展示过某个练习就标记掌握。
- 对话练习必须服务于输出质量和复盘，不应退化成无目标闲聊。

### 3. Retrieval: 复述、改写和回忆优先于被动解释

已有 skill 实践把 lesson 固定为 `Scene Capsule -> High-Value Chunks -> Comprehension Check -> Error-Prone Rewrite -> Contextual Output -> Profile Delta + Review Candidates`。这个顺序的价值在于：先建立语境，再选择少量目标，然后强制学习者检索和生成。

产品含义：

- MVP 中每个 lesson 或 pattern 至少应包含一个主动生成动作。
- Review item 不应只是词条收藏；它应说明下一次如何检索、改写或迁移使用。
- 复盘应区分“看懂了”“刚练过”“延迟后还能取出”。

### 4. Spacing: 复习是闭环，不是附加功能

EnglishLearningWorkflow 的记录显示，复习 session 数量明显多于新 lesson，CORA 也把 D+1/D+3/D+7 返回作为流程的一部分。这说明长期价值不在第一次生成 lesson，而在后续能否把旧材料重新变成输出任务。

产品含义：

- MVP 可以不实现完整 SRS，但必须有 `ReviewItem`、`due_at` / `status` / `source_session_id` 等可扩展字段。
- 默认 review 入口应 summary-first：先告诉用户今天最值得复习什么，再展开少量项目。
- 用户应能 pause、ignore、delete、archive 或 mark mastered，且这些行为应留下事件痕迹。

### 5. Formulaic Language: 口语优先训练语块完整性

live-chat lesson 和 CORA session 都反复暴露同一个问题：学习者能理解单词，但输出时会把固定 chunk 拆坏，或把自然搭配翻译成不自然结构。

产品含义：

- `live_chat`、roleplay、CORA 这类口语/对话 pattern 应优先选择 reusable chunks，而不是大词表。
- 反馈应记录 chunk integrity，例如 `take some getting used to`、`tap someone on the shoulder`、`the joke falls flat` 是否被完整取出。
- Review item 应支持 chunk-level key，而不是只支持单词。

## 从实践中得到的约束

### 输入材料必须先变成 lesson-ready text

原始字幕常有编号、时间戳、滚动字幕重复、断行、ASR 噪音和误识别。直接从 raw subtitle 抽词会破坏语境，也会让练习目标变随机。

LinguaLoop 应保留以下管线概念：

```text
raw source -> normalized text -> lesson-ready text -> segment -> lesson/session
```

每个阶段都应可追踪，但 MVP 不必一次性实现复杂导入器。

### Track 是教学策略，不是文件后缀

同样是 subtitle，可能是 live chat，也可能是 documentary narration。前者需要互动语气、语块和场景输出；后者需要论点理解、连接词、概括和改写精度。

因此 `track` 应成为 `LearningMaterial` / `MaterialAnalysis` / `PracticePlan` 的业务属性之一，不能只从文件扩展名推断。

### 分段策略应保护语境

经验 workspace 采用 medium segmentation：不要一整场视频塞进一节课，也不要把 setup/payoff、claim/support 或互动回合切碎。

LinguaLoop 的 segment 至少需要：

- `start_ref` / `end_ref`
- `scene_or_argument_summary`
- `context_before_summary`
- `context_after_summary`
- `track`

### Profile 是证据快照，不是人格判断

Profile Delta 应记录当前学习暴露出来的能力变化，例如可复用 chunks、输出脆弱点、下一步焦点，而不是给学习者贴长期标签。

系统内应区分：

- `SessionEvent`: 发生过的事实。
- `FeedbackItem`: 针对某次输出的纠错证据。
- `ReviewItem`: 可再次检索的练习候选。
- `UserProfile` / learner profile: 从历史证据汇总出的当前快照。

### CORA 和输入 lesson 是两个 pattern 家族

输入 lesson 解决“从真实材料里学什么”；CORA 解决“已经知道的表达能不能快速说出来”。二者可以共享 review items 和 profile evidence，但不应混成同一个流程。

CORA 的四段结构值得保留为独立 pattern：

```text
Cold attempt -> Observe -> Rebuild -> Automate
```

它给 LinguaLoop 一个重要产品边界：不要把更多输入误认为口语自动化，也不要让 model answer 污染冷启动测量。

## 对 MVP 的要求

第一版 MVP 至少要体现这些行为：

1. 创建材料时保留 source / track / language / text 的最小合同。
2. 材料分析输出摘要、目标表达、难点和建议练习目标。
3. 会话必须要求用户输出，而不是只展示解释。
4. 反馈必须能关联到用户消息或源材料片段。
5. 复盘必须生成结构化 review candidates。
6. Review 入口应 summary-first，避免一次展示大量复习项。
7. Profile 更新只基于真实表现证据。

## 架构含义

这些原则支持当前 Core / Kernel / Pattern / Plugin 的分层：

- `core`: 定义稳定学习对象，如 material、segment、session、message、feedback、review、profile、event、pattern manifest 和 capability requirement。
- `kernel`: 推进学习流程，决定何时调用 pattern、provider、event store 和 review policy。
- `patterns`: 表达“怎么学”，例如 input lesson、guided roleplay、retell、CORA、spaced review。
- `plugins`: 表达“能做什么”，例如 LLM、STT、TTS、subtitle importer、voice session 和 avatar renderer。
- `engine adapters`: 表达“用什么 runtime 跑”，例如 direct runner 或 LangGraph。

## 边界和风险

- 外部研究支持的是方向，不证明 LinguaLoop 模板唯一最优。
- 本地实践样本来自一个主要学习者和英语场景，不能直接推断所有语言、所有水平和所有材料类型。
- `EnglishLearningWorkflow` 当前更像经验型工作区，不是产品级数据模型；LinguaLoop 应吸收其结构经验，而不是原样复制其目录和脚本。
- 用户材料、答案和学习画像都应按敏感数据处理；公开文档只能沉淀抽象经验，不应提交私有路径、完整答案或可识别学习记录。

## 待验证问题

- `track` 是否只保留 `live_chat` / `article_reading` 两类，还是 MVP 就加入 `spoken_retrieval`。
- Profile Delta 如何从 session 级别汇总成长期 learner profile，避免过度诊断。
- Review item 的最小调度字段和用户控制字段如何定型。
- 输入 lesson、guided roleplay、retell、CORA 是否共享一个 `PracticePlan` contract，还是需要 pattern-specific state。
- LangGraph adapter 何时接管 direct runner，以及哪些事件必须由 kernel 统一写出。
