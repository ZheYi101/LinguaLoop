# 文档目录

本文档目录按读者意图分类。新文档优先放入对应子目录，避免所有内容堆在 `docs/` 根目录。

## Product

- [Project Brief](./product/PROJECT_BRIEF.md): 项目愿景、目标用户、产品原则和非目标。
- [MVP Spec](./product/MVP_SPEC.md): 第一版 MVP 范围、用户故事、初始数据对象和验收标准。

## Research

- [Learning Loop Foundation](./research/LEARNING_LOOP_FOUNDATION.md): 语言学习闭环的理论基础、实践约束和架构含义。
- [Practice Workspace Findings](./research/PRACTICE_WORKSPACE_FINDINGS.md): 从既有 input-driven skill 和 EnglishLearningWorkflow 经验样本中提取的产品与数据模型经验。

## Architecture

- [Architecture](./architecture/ARCHITECTURE.md): 初始系统架构、模块边界和关键用例。
- [Agent Core Architecture](./architecture/AGENT_CORE_ARCHITECTURE.md): Python-first Agent Kernel、LangGraph adapter 和 typed LLM 调用规划。
- [Extension Architecture](./architecture/PLUGIN_ARCHITECTURE.md): Core / Plugins / Patterns 三层扩展架构。
- [Learning Patterns](./architecture/LEARNING_PATTERNS.md): input lesson、guided roleplay、review、CORA 等学习 Pattern 的分类和共同不变量。
- [Core Concepts](./architecture/CORE_CONCEPTS.md): 当前 `src/lingualoop/core` 中核心模型、Provider、EventStore 和常见 Python/Pydantic 写法说明。

## Planning

- [Roadmap](./planning/ROADMAP.md): Phase 0 到 Phase 3 的开发路线图。

## Decisions

- [Technical Decisions](./decisions/TECH_DECISIONS.md): 会影响长期维护的技术决策记录。

## Root Documents

- [Repository Guide](../AGENTS.md): coding agents 的仓库工作约定。
- [Contributing](../CONTRIBUTING.md): 开源贡献规范。
