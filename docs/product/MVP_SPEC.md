# MVP Spec

## MVP 目标

第一版目标是验证一个核心闭环：用户导入材料后，可以围绕材料完成一次对话练习，并获得结构化复盘和后续练习建议。

## 核心流程

1. 用户创建或导入学习材料，输入标题、目标语言、母语和原文内容。
2. 系统分析材料，生成摘要、关键词、表达点和推荐练习目标。
3. 用户选择练习目标和难度，开始对话。
4. AI 在对话中围绕材料语境互动，并在必要时提供提示或即时纠错。
5. 用户主动结束练习后，系统生成复盘：表现摘要、错误类型、推荐表达、复习项和下一次任务。
6. 复习项保存到本地 review queue，下次启动软件仍可查看并继续复习。

## MVP 功能范围

- 材料管理：创建、查看、编辑、删除文本材料，支持 Markdown 和 DOCX 导入。
- 材料分析：摘要、关键词、常用表达、潜在难点。
- 对话练习：基于材料的多轮文本对话。
- 即时反馈：轻量纠错、替代表达、追问和提示。
- 练习复盘：会话摘要、错误记录、推荐复习项，结束会话时集中生成 review candidates。
- 本地持久化：用 SQLite 保存材料、会话、消息、反馈、复盘和 review queue。
- 基础复习：支持 `again`、`hard`、`good`、`easy` 结果记录和简单 due date 更新。
- 基础设置：目标语言、用户母语、难度、纠错强度。
- 最小扩展基础：内置文本学习 Pattern、LLM provider plugin contract、capability requirement check、provider mock。

## 学习方法约束

MVP 不需要一次性实现完整课程系统或 SRS，但必须体现以下学习闭环约束：

- 输入材料需要进入可教学状态。至少要区分 raw text、lesson-ready text 和后续 segment；不要直接从带时间戳、断行、重复 cue 或明显 ASR 噪音的字幕中抽取练习目标。
- `track` 是显式业务属性，不应只由文件后缀推断。`live_chat` 更关注互动语气和口语 chunk；`article_reading` 更关注论点、连接词、概括和改写精度。
- 每次练习必须包含一个主动输出动作，例如改写、复述、场景对话或短 summary；只展示解释不算完成学习闭环。
- 反馈必须关联到用户真实输出或源材料片段，优先记录反复出现的 pattern-level 问题，而不是堆叠所有小错。
- 复盘必须生成结构化 review candidates，即使第一版只实现简单 `due_at` 和 `status`，也要为后续 spaced review 留接口。
- Profile Delta 只能表示本轮学习证据，不能把一次回答包装成长期能力结论。

理论和实践依据见 [Learning Loop Foundation](../research/LEARNING_LOOP_FOUNDATION.md) 与 [Practice Workspace Findings](../research/PRACTICE_WORKSPACE_FINDINGS.md)。

## 暂不包含

- 生产级语音识别和语音合成；语音能力作为后续 `voice-livekit` 插件验证。
- 移动端原生应用。
- 多人社区、排行榜、课程交易。
- 完整 SRS 算法。
- 复杂教师后台。
- Live2D / avatar 渲染；作为后续表现层插件验证。

## 用户故事

- 作为学习者，我可以粘贴一段目标语言材料，并让系统帮我提取可练习表达。
- 作为学习者，我可以围绕这段材料进行对话，而不是进行无上下文闲聊。
- 作为学习者，我可以控制 AI 纠错强度，避免对话被频繁打断。
- 作为学习者，我可以在结束后看到我常犯的错误和下一次该练什么。

## 初始数据对象

- UserProfile: 用户语言、目标、偏好设置。
- LearningMaterial: 标题、语言、来源、正文、分析结果。
- PracticeSession: 材料、目标、难度、消息列表、状态。
- Message: 角色、内容、时间、反馈引用。
- FeedbackItem: 错误类型、原句、建议句、解释、复习状态。
- LearningSegment: 材料片段、来源位置、上下文和练习目标。
- ReviewItem: 表达、例句、来源会话、来源材料、状态、下次复习时间。
- ReviewOutcome: 复习回答、结果评级、发生时间和下一次复习时间。
- SessionReview: 会话摘要、重点问题、review candidates 和下一步建议。
- SessionEvent: 会话中可追踪、可回放的学习事件。
- PracticePlan: 学习 Pattern 生成的一次练习计划。

## 验收标准

- 用户可以完成从材料创建到会话复盘的端到端流程。
- 用户可以导入 `.md`、`.markdown` 和 `.docx` 材料并保留 raw/normalized 文本边界。
- 对话内容能稳定引用材料语境，不退化成泛用聊天。
- 复盘内容以结构化数据保存，而不仅是纯文本总结。
- 会话未结束前不生成最终 review queue；用户主动结束后才集中生成复习项。
- 重启软件后仍可看到已保存材料、会话摘要和 review queue。
- 用户可以对复习项记录 `again`、`hard`、`good`、`easy` 并更新下次复习时间。
- LLM 调用失败时有可理解的错误提示，不丢失用户当前输入。
- 用户数据和配置不依赖硬编码示例。
- 内置学习 Pattern 通过稳定 contract 生成练习计划和复盘草稿，并声明所需 capability。
- 系统不会把“生成过 lesson”或“展示过复习项”计为掌握；只有用户输出、复习结果或延迟检索结果能更新学习状态。
- Review 入口默认 summary-first，先给 1-3 个复习方向，再按需展开具体条目。
