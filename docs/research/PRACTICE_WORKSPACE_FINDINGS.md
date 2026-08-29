# Practice Workspace Findings

本文档总结从 `input-driven-language-coach` skill 和 EnglishLearningWorkflow 经验工作区中提取的设计经验。目标不是迁移旧项目，也不是公开个人学习记录，而是把已有实践转化为 LinguaLoop 的产品、数据和 agent kernel 约束。

## 审计边界

- 本次只读参考 `input-driven-language-coach` skill、其 references/scripts，以及 EnglishLearningWorkflow 的材料、lesson、session、review 和 CORA 记录。
- 不修改参考 skill 或经验工作区。
- 不在本文保存本地绝对路径、完整学习答案、cookie、密钥或个人学习日志全文。
- 经验样本主要来自英语学习，不能自动推广到所有语言和水平。

## 样本概况

EnglishLearningWorkflow 当前呈现出一个已经实际使用过的轻量学习系统，而不是纯设计稿。

按文件类型看，样本包含：

| 类型 | 数量 | 说明 |
| --- | ---: | --- |
| Markdown | 144 | lesson、session、feedback、review、CORA 记录和说明文档 |
| VTT | 39 | 主要是字幕源材料 |
| TXT | 16 | 清洗或 lesson-ready 文本 |
| JavaScript | 8 | 字幕清洗、渲染、导入和测试脚本 |
| SRT | 4 | 字幕源材料 |
| JSON | 2 | 规范化字幕或配置类文件 |
| ASS | 1 | 字幕源材料 |

在 `languages/en` 下，观察到以下结构：

| 区域 | 数量 | 作用 |
| --- | ---: | --- |
| raw | 8 | 原始导入材料 |
| cleaned | 16 | lesson-ready 文本和 Markdown |
| segments | 68 | 可教学片段 |
| lessons | 6 | 输入驱动 lesson |
| sessions | 49 | 答案、反馈、复习和索引记录 |

`sessions` 中 review 类记录明显多于新 lesson 记录。这对 LinguaLoop 很重要：真实使用时，价值不会停在“生成一节课”，而是在后续复习、再输出和纠错中继续产生。

## 经验系统的两条主线

### 1. Input-driven lesson

Input-driven lesson 解决的问题是：用户已经看过或读过一段材料，如何把这段材料转成可练、可纠错、可复习的学习任务。

观察到的稳定结构：

```text
Scene Capsule
High-Value Chunks / Vocab
Comprehension Check
Error-Prone Rewrite
Contextual Output
Profile Delta + Review Candidates
```

这套结构的实际价值在于：

- `Scene Capsule` 先恢复语境，避免词汇教学脱离说话意图或论证结构。
- `High-Value Chunks / Vocab` 控制目标数量，优先可复用项目。
- `Comprehension Check` 让学习者重新处理输入，而不是只听解释。
- `Error-Prone Rewrite` 主动暴露高概率生产错误。
- `Contextual Output` 要求学习者在原语境或同类语境中输出。
- `Profile Delta + Review Candidates` 把本轮暴露的问题留给后续复习。

### 2. CORA spoken-retrieval practice

CORA 解决的问题不同：学习者已经大致懂某些表达，但在真实口语中无法快速、稳定地取出。

观察到的稳定结构：

```text
Cold attempt -> Observe -> Rebuild -> Automate
```

这套结构给 LinguaLoop 的关键启发是：

- 冷启动输出是测量，不应先展示 model answer。
- 每轮最多修三个 production fractures，避免纠错过载。
- 训练目标应限制为一个主题、三个 chunks、一个 grammar target。
- 自动化来自压缩、迁移和延迟回忆，而不是读熟一段标准答案。
- 进步应从冷启动或延迟输出中判断，而不是从刚排练过的 polished attempt 判断。

## 输入处理经验

### Raw source 不能直接教学

经验工作区保留了 `raw`、`cleaned`、`segments`、`lessons` 和 `sessions` 的分层。这说明字幕和 transcript 在成为 lesson 前需要经过至少两个概念阶段：清洗和切分。

LinguaLoop 应抽象出以下生命周期：

```text
SourceMaterial -> NormalizedMaterial -> LearningSegment -> PracticePlan -> PracticeSession
```

不要把用户粘贴的一整段 raw text 直接等同于可教学材料。尤其是字幕：时间戳、断行、重复 cue、ASR 误识别和字幕格式会污染目标选择。

### Track 决定练法

经验样本显示，材料形式和教学 track 不能简单绑定：

- 直播/闲聊材料适合 `live_chat`：重点是语气、互动、自然口语 chunk 和场景输出。
- 历史纪录片或解释型字幕适合 `article_reading`：重点是论点、因果、对比、概括和改写精度。
- 动作/词汇类视频虽然来自字幕，但实际 lesson 更接近 feature-based article/explanation，因为它要区分 force、direction、body part 和 social meaning。

结论：`track` 是业务选择，不是文件后缀。

### Medium segmentation 是合理默认

经验工作区中的 segment 数量远多于 lesson 数量，说明材料可以先被切成多个可教学单元，再按学习进度消费。

合理分段应该：

- 足够短，可以完成一轮练习。
- 足够完整，保留 scene、setup/payoff、claim/support 或动作分类逻辑。
- 带上前后文摘要，便于复习时不重读全文也能恢复语境。

LinguaLoop 不应默认使用固定字数切分。不同 track 至少需要不同的 segment policy。

## Lesson 设计经验

### Live chat lesson: 语气和互动优先

live-chat 样本中，高价值目标不是生词，而是带语气和互动功能的表达，例如“需要适应”“让两群人相处”“解释临时方案”“降低突兀感”。这类目标的复用价值来自场景功能。

对 LinguaLoop 的启发：

- `MaterialAnalysis` 应能记录 scene intent 和 tone。
- `PracticeInstruction` 应能要求用户在相同互动场景中输出，而不是只造句。
- `FeedbackItem` 应能标记 fixed chunk 被拆坏、语气不自然、场景功能偏离。

### Article reading lesson: 论证结构优先

Napoleon 系列样本使用纪录片字幕作为 `article_reading`，重点不是口语模仿，而是历史语境、政治/军事评价、对比和 turning-point 叙述。

对 LinguaLoop 的启发：

- `article_reading` 的 `Scene Capsule` 实际上应更像 `Argument Capsule`。
- 输出任务应要求 80-150 词摘要、立场改写或论证重述。
- Review item 应覆盖 connector、stance framing、abstract collocation，而不是只覆盖词义。

### Feature-based vocabulary lesson: 近义词要按特征分组

body-action lesson 显示，词汇学习不应只给中文释义。像 `tap`、`poke`、`grab`、`squeeze`、`pinch`、`pat`、`pet` 这类词，需要按 force、direction、body part、duration、social meaning 分组。

对 LinguaLoop 的启发：

- `MaterialExpression` 不应只保留 `text` 和 `meaning`，后续可以扩展 `contrast_set`、`usage_features` 或 `common_confusions`。
- 纠错需要解释“为什么这个词不适合这个场景”，而不是只给正确答案。
- Review item 可以是 contrast drill，例如从场景选择 `tap` vs `poke`。

## Feedback 设计经验

### 纠错要优先 pattern，不要追逐所有小错

session feedback 中反复出现的有效做法是：先给直接修正，再总结 pattern，例如 tense consistency、body-part pattern、return pattern、complex noun phrase、chunk integrity。

LinguaLoop 的 `FeedbackItem` 应能承载：

- 错误类型。
- 原句和改句。
- 解释。
- 来源 message / segment。
- 是否形成 review candidate。
- 后续可选的 difficulty / outcome，例如 `again`、`hard`、`good`、`easy`。

### 复习反馈要记录结果，而不是只讲解

review feedback 样本会给每个项目标注 `again`、`hard`、`good`、`easy` 等结果。这是最小 SRS 的雏形。

LinguaLoop MVP 不一定需要完整算法，但需要保留 outcome 字段或事件，以便将来更新 `due_at`、`interval_days`、`stability` 和 `priority_score`。

### 用户可以跳过，系统不能假装掌握

review 样本中有 learner-requested skipped round，并明确写出“不能从跳过项推断 mastery”。这是重要产品原则。

LinguaLoop 应把 skip / pause / ignore / delete / archive / mastered 都设计成用户动作或事件，不应静默删除 review item。

## Profile 经验

Profile Delta 的有效形态是“本轮证据摘要”，不是长期人格判断。

实践中最有用的字段包括：

- `comprehension_strengths`: 本轮明确能处理什么。
- `output_fragilities`: 输出中暴露的脆弱点。
- `reusable_chunks`: 值得后续复用的语块。
- `next_focus`: 下一步最值得练什么。
- `review_candidates`: 应进入复习池的项目。

LinguaLoop 应将长期 profile 视作从 session events、feedback 和 review outcomes 重建的快照，而不是让 LLM 任意改写一个大 profile 文件。

## CORA 对产品边界的启发

CORA 样本特别说明：输入变多不等于口语自动化变强。LinguaLoop 的产品设计应把“输入驱动学习”和“口语检索训练”分成两个 pattern 家族。

可以共享的部分：

- chunks。
- feedback categories。
- review items。
- learner profile evidence。
- delayed recall schedule。

必须分开的部分：

- CORA 的冷启动测量不能被 input lesson 的 model answer 污染。
- CORA 每轮只允许少量目标，不能继承 lesson 的完整词汇清单。
- CORA 的进步指标是启动延迟、弃句、chunk retrieval、grammar stability 和 message completion，而不是 lesson 完成数。

## 数据模型启发

经验工作区支持 LinguaLoop 继续采用事件和快照分离：

```text
Material / Segment
  描述输入材料和可教学单位

PracticeSession
  聚合当前练习状态

SessionEvent
  保存发生过的事实

FeedbackItem
  保存对真实输出的纠错证据

ReviewItem
  保存未来可检索的任务

LearnerProfile
  从历史证据汇总出的当前快照
```

其中 `SessionEvent` 应成为长期事实来源，`LearnerProfile` 应可重建，`ReviewItem` 应可被用户控制。

## MVP 应吸收的经验

第一版不需要复制整个 EnglishLearningWorkflow，但应该吸收以下最小能力：

1. 显式输入合同：material type、track、title、target language、native language、text/source。
2. 清洗状态：至少区分 raw text 和 lesson-ready text。
3. Segment metadata：start/end ref、scene/argument summary、前后文摘要。
4. 两类基础 pattern：input-derived conversation/retell 和 summary-first review。
5. 反馈闭环：用户输出 -> direct correction -> pattern summary -> review candidates。
6. Profile Delta：本轮证据快照，而不是长期定性判断。
7. 用户控制：允许跳过、暂停、忽略、删除或归档复习项，并保留事件。

## 不应直接照搬的部分

- 旧工作区脚本是 Node.js，LinguaLoop core 已确定 Python-first；应迁移思想，不迁移技术栈约束。
- 旧工作区目录是个人学习工作流，不应成为公开产品的固定用户路径。
- 旧 lesson 六段结构适合 input-derived lesson，但 CORA、roleplay、shadowing 和 review 不应被强塞进同一模板。
- 旧工作区没有形成完整产品级权限、隐私、同步和多用户模型，LinguaLoop 后续需要重新设计。
- 当前样本没有发现 `.sql` 文件；已有持久化思路主要体现在文档、Markdown 记录、脚本和 workspace schema，而不是可直接迁移的 SQL schema。

## 对后续文档工作的建议

- 在 `docs/product/MVP_SPEC.md` 中明确 MVP 的 method constraints：cleaning、track、active output、feedback evidence、review candidates。
- 在 `docs/architecture/ARCHITECTURE.md` 中补充 material lifecycle 和 profile/event separation。
- 在 `docs/architecture/AGENT_CORE_ARCHITECTURE.md` 中把 CORA 作为后续 pattern 家族，而不是混入 guided roleplay。
- 在 `docs/decisions/TECH_DECISIONS.md` 中记录“研究启发 + 实践经验驱动的学习闭环”决策，避免未来把产品改回 generic chatbot。
