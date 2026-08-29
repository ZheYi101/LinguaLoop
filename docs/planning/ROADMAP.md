# Roadmap

## Phase 0: 项目定义

- [x] 初始化基础文档
- [ ] 确定开源许可证
- [ ] 确定第一版技术栈
- [ ] 确定 MVP 的首个目标语言和示例材料
- [ ] 定义插件 manifest、capability registry 和权限模型 v0
- [ ] 定义 Pattern manifest、capability requirements 和第一批学习 Pattern 清单
- [x] 确认 Python-first Agent Kernel 方案并将 Decision 0004 升级为 Accepted
- [x] 沉淀真实输入学习闭环的理论依据和 EnglishLearningWorkflow 实践经验

## Phase 1: 可运行 MVP

- [ ] 创建应用脚手架
- [ ] 实现 Python core Pydantic models 和 session event schema
- [ ] 实现 material lifecycle：raw source、lesson-ready text、segment metadata
- [ ] 实现 Agent Kernel 的 direct deterministic runner
- [ ] 实现材料创建和管理
- [ ] 实现材料分析 pipeline
- [ ] 实现基于材料的文本对话
- [ ] 实现会话复盘和 review items
- [ ] 实现 review outcome 和用户控制事件：again、hard、good、easy、pause、ignore、delete、archive、mastered
- [ ] 实现最小 plugin registry
- [ ] 实现 capability requirement check
- [ ] 实现内置 input-derived 文本学习 Pattern
- [ ] 实现 LangGraph AgentEngine adapter
- [ ] 增加 LLM provider mock 和基础测试

## Phase 2: 学习闭环增强

- [ ] 增加练习目标模板
- [ ] 增加纠错强度和难度设置
- [ ] 增加 roleplay / shadowing / retell 学习 Pattern
- [ ] 增加复习列表和基础提醒
- [ ] 增加 spaced-review 调度 Pattern
- [ ] 增加 CORA spoken-retrieval Pattern：Cold attempt、Observe、Rebuild、Automate
- [ ] 增加会话历史搜索
- [ ] 增加学习进度概览

## Phase 2.5: 多模态插件验证

- [ ] 实现 `voice-livekit` 插件原型
- [ ] 记录语音延迟、打断响应、STT partial 稳定性和单轮成本
- [ ] 实现 `avatar-live2d` 插件原型
- [ ] 验证 Pattern 与语音 modality / plugin capability 的组合方式
- [ ] 评估是否需要把语音插件升级为 voice subsystem

## Phase 3: 开源可协作

- [ ] 完成开发环境文档
- [ ] 增加 issue / PR 模板
- [ ] 增加示例数据和 demo workflow
- [ ] 完成隐私和数据导出说明
- [ ] 完成部署说明
- [ ] 完成第三方插件开发指南
- [ ] 完成第三方 Pattern 开发指南
