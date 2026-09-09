# LinguaLoop UI 页面规划

## 方向

桌面端和 Android 端共享 PySide6/QML 页面，基础控件使用 Qt Quick Controls 6，应用壳使用 Kirigami。桌面端采用左导航、中工作区、右上下文的工作台结构；移动端不是桌面三栏布局的窄化版本，而是围绕当前学习动作的单列流程：

```text
材料 -> 分析 -> 练习 -> 用户输出 -> 反馈 -> 复盘
```

## 页面

### 材料

用户可以粘贴文本或导入 `.md`、`.markdown`、`.docx` 文件。材料页收集标题、正文、材料语言、目标语言、母语、等级和 track。点击分析后展示摘要、关键词、表达、难点和推荐目标，再进入练习。

桌面端可以在主区域展示编辑器和分析结果；移动端使用单列表单和可滚动分析结果。

### 练习

展示当前任务、对话记录和输入框。发送期间显示 loading，重复提交被禁止；请求失败时保留用户输入并展示错误。桌面端右侧显示材料摘要、当前任务和少量 review queue；移动端优先保证对话和输入区域可用。

练习页提供“结束并复盘”，用户可自由多轮回答。最终 review candidates 只在结束时生成。

### 复盘

展示会话摘要、反馈项和 review items，并提供 JSON 导出。复习项支持先输入答案，再记录 `Again / Hard / Good / Easy`，并可暂停或归档。桌面端可同时展示更多细节；移动端默认先展示摘要和重点项，详细内容通过滚动查看。

### 导航和设置

第一版导航为材料、练习、复盘和设置入口。宽桌面使用左侧栏，900px 以下隐藏右侧上下文，600px 以下改用顶部 TabBar。设置页暂不实现 provider 配置，只说明真实 provider 模式和本地数据目录。

## CLI 映射

| CLI 命令 | 页面能力 |
| --- | --- |
| `load` | 材料页创建和分析 |
| `import` | 材料页导入 Markdown/DOCX |
| `start` | 从材料页进入练习页 |
| `say` | 练习页发送回答 |
| `finish` | 练习页结束并生成复盘 |
| `review` | 复盘页复习项 |
| `rate` | 复习页记录 outcome |
| `summary` | 复盘页摘要 |
| `export` | 复盘页导出 |
| `reset` | 应用级重置 |

首版不做完整课程、账户、云同步、语音、历史搜索和完整 SRS 调度。运行时持久化使用本地 SQLite。

## UI 边界

QML 只依赖 Python ViewModel 的 properties、signals 和 slots。ViewModel 调用 `LearningWorkbench`，将 Pydantic 对象转换为 QML 可用的稳定 DTO。网络请求不阻塞 UI，错误不丢失输入。
