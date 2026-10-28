# LinguaLoop

LinguaLoop 是一个把沉浸式输入转化为语音输出练习的开源语言学习伙伴。**沉浸提供语境，LinguaLoop 帮你练输出。** 看番、追视频、听播客或读文章后，让 AI 先理解对应材料、推荐几个可聊话题，再围绕共同内容练习语音对话；也可以自愿进入语境 roleplay。

## 当前状态

项目处于早期 MVP 阶段。当前开发先验证纯文本：材料导入 → 推理模型分块整理大纲、人物、丰富话题及常见回答分支 → 选择或现场整理自定义话题 → Flash 模型流式自然讨论。已有 MD3 桌面、SQLite 恢复与分轮语音适配器；STT/TTS 暂不作为本阶段开发依赖。后续连续语音使用 LiveKit，必须在文本功能独立验收后推进。

主要使用 DeepSeek 的 `deepseek-v4-pro`（思考模式）与 `deepseek-flash`（非思考模式）。Pro 负责材料与自定义话题准备，并在后台按需预测可能的下一轮意图；Flash 仅根据短上下文、已准备资料和用户真实发言回复。预测只作候选参考，不能成为“用户说过的话”。首字延迟与完整回复耗时分别测量，**流式显示不代表完整回复已达到 1 秒目标**。

业务、模拟语音和 QML 点击路径已通过自动验证。真实麦克风与云端语音的三轮验收仍待完成，不能用 mock 通过代替。当前完成情况和限制见 [初版验证记录](./docs/planning/INITIAL_VERSION_2026-10-24.md)。

## 产品方向

LinguaLoop 面向已经在进行沉浸输入、希望把熟悉内容转化为口语表达的学习者。用户继续按兴趣消费内容，项目负责提供有共同语境的输出机会。默认先讨论内容，roleplay 可选；学习方法和反馈节奏逐步支持配置。

核心学习闭环：

1. 带入已经看过、听过或读过的字幕、转写或文本
2. AI 理解语境，推荐几个有材料依据的话题
3. 选择话题，用语音自然讨论，或自愿进入语境 roleplay
4. 根据偏好获得提示、纠错和替代表达
5. 结束后轻量复盘，下次再练值得巩固的表达

当前主旨以 [Project Brief](./docs/product/PROJECT_BRIEF.md) 为准；用户无需先完成词汇课或理解测验才能开聊。

## 文档导航

- [AGENTS.md](./AGENTS.md): 给 Codex / coding agents 的仓库工作规则
- [docs/README.md](./docs/README.md): 文档目录入口和分类导航
- [docs/product/PROJECT_BRIEF.md](./docs/product/PROJECT_BRIEF.md): 项目愿景、用户和产品原则
- [docs/product/MVP_SPEC.md](./docs/product/MVP_SPEC.md): 第一版 MVP 范围和验收标准
- [docs/architecture/ARCHITECTURE.md](./docs/architecture/ARCHITECTURE.md): 初始系统架构和模块边界
- [docs/architecture/CORE_CONCEPTS.md](./docs/architecture/CORE_CONCEPTS.md): Core 领域对象、Provider、EventStore 和 Python/Pydantic 基础概念
- [docs/architecture/PLUGIN_ARCHITECTURE.md](./docs/architecture/PLUGIN_ARCHITECTURE.md): Core / Plugins / Patterns 三层扩展架构
- [docs/architecture/AGENT_CORE_ARCHITECTURE.md](./docs/architecture/AGENT_CORE_ARCHITECTURE.md): Python-first Agent Kernel、LangGraph adapter 和 typed LLM 调用规划
- [docs/decisions/TECH_DECISIONS.md](./docs/decisions/TECH_DECISIONS.md): 技术决策记录和待定项
- [docs/planning/ROADMAP.md](./docs/planning/ROADMAP.md): 开发路线图
- [CONTRIBUTING.md](./CONTRIBUTING.md): 开源贡献规范

## 本地验证

安装开发依赖后，可以运行当前测试：

```bash
python -m pytest
```

使用 `uv` 时推荐：

```powershell
uv sync --dev --extra desktop
.venv\Scripts\python.exe -m pytest -q
```

离线验证前请保证 `RUN_REAL_AI_TESTS=0`。生成带显式字体加载的演示截图：

```powershell
.venv\Scripts\python.exe scripts\render_ui_preview.py
```

截图保存在 `build/ui-preview/`，使用临时演示数据，不读取个人学习数据库或 `.env`。

## 下一步

围绕当前主旨，优先补齐以下能力（详细范围见 MVP 和路线图）：

1. 用用户提供的完整《Lolita》验证准备资料、真实 Flash 多轮讨论的质量和首字/完整回复延迟；当前分段准备已保存，真实讨论仍受账户余额阻碍。
2. 文本验收后实现 LiveKit 连续对话，再选择适合未来用户接入的 STT/TTS 服务。
3. 补齐平台发行包、Pattern / capability contract，并确定项目开源许可证。

## 真实 AI 冒烟测试

默认 `python -m pytest` 不应调用真实模型。要测试从 LangGraph 到 OpenAI-compatible provider 再到真实模型的完整链路，请在本地 `.env` 配置：

```dotenv
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_REASONING_MODEL=deepseek-v4-pro
OPENAI_DIALOGUE_MODEL=deepseek-flash
OPENAI_DISABLE_THINKING=1
OPENAI_REASONING_THINKING=1
OPENAI_DIALOGUE_THINKING=0
RUN_REAL_AI_TESTS=1
```

DeepSeek 双模型默认明确分工：推理角色 `thinking.type=enabled`、`reasoning_effort=high`，对话角色 `thinking.type=disabled`。旧 `OPENAI_DISABLE_THINKING=1` 仅影响对话默认值，不再全局关闭推理。通用兼容服务可用两个新变量分别覆盖；不支持 thinking 参数的服务请留空这些变量并将旧项设为 0。模型名称参见 [DeepSeek 官方模型表](https://api-docs.deepseek.com/quick_start/pricing/) 和 [思考模式](https://api-docs.deepseek.com/guides/thinking_mode/)，对话输出不保存或展示思维链。

如果不确定服务可用模型名，先运行：

```powershell
.venv\Scripts\python.exe scripts\list_openai_models.py
```

再把返回列表里的模型 id 填到 `OPENAI_REASONING_MODEL` 和 `OPENAI_DIALOGUE_MODEL`。然后运行真实 AI 冒烟测试：

```powershell
.venv\Scripts\python.exe -m pytest tests\test_llm.py -q
```

不要提交 `.env` 文件；仓库已在 `.gitignore` 中忽略本地环境文件。

## CLI POC

现在已经有一个无 UI 的命令行原型，可以先验证完整闭环：

```powershell
lingualoop --mock
```

如果还没把项目同步进当前环境，先执行 `uv sync --dev`，或者临时用 `PYTHONPATH=src` 再运行。

常用命令：

- `load`：加载并分析材料
- `import`：导入 `.txt`、`.md`、`.markdown`、`.docx`、`.srt`、`.vtt`、`.epub` 或 `.xlsx` 材料，并确认标题、track 与 normalized preview
- `start`：开始一次练习会话
- `say`：发送用户回答
- `finish`：结束本轮并生成结构化复盘和 review items
- `review`：查看今日到期复习项
- `review --all`：查看全部 active 复习项
- `rate`：记录 `again`、`hard`、`good` 或 `easy` 复习结果；`good/easy` 会先做最小答案校验
- `summary`：查看当前会话摘要
- `export`：导出会话 JSON
- `reset`：清空当前选择状态，不删除本地持久化数据
- `quit`：退出

默认模式会读取 `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_REASONING_MODEL` 和 `OPENAI_DIALOGUE_MODEL`。离线调试可用 `--mock`。

## MD3 桌面初版

桌面端采用 Python ≥3.11、PySide6 6.11.1、QML 和 Qt Quick Controls Material。Windows 默认使用 ApplicationWindow，安装 PySide6 即可运行。Kirigami 仅作为显式启用的可选壳：

```powershell
uv sync --extra desktop
```

启动桌面工作台。桌面端默认使用真实 OpenAI-compatible provider，并读取当前工作目录 `.env` 或系统环境变量中的 `OPENAI_*` 配置：

```powershell
uv run lingualoop-desktop
```

离线调试时可以显式使用 mock provider，不需要真实 API key：

```powershell
uv run lingualoop-desktop --mock
```

普通启动缺少或无法解析 AI 配置时，会进入本地资料模式，仍可查看已保存的材料和历史；需要模型的操作明确报错，不会自动生成模拟回答。服务余额不足时，本地资料也可打开，在线操作显示服务错误。

界面默认跟随系统主题，可切换浅色、深色及减少动效。主要围绕材料和对话；复盘、设置作为辅助入口。宽度小于 600 使用底部导航；600–1199 使用 80px 导航 rail；1200 起对话页可显示 320px 语境面板。

## 材料准备与快速文本讨论

EPUB 按书内 spine 阅读顺序抽取文字并去除 ruby 注音、脚本与样式；Excel 按工作表和行抽取单元格缓存值，不执行公式。视频 `.mp4/.mkv/.webm/.mov/.avi` 只导入同目录同名 `.srt` 或 `.vtt`，当前模型未读取视频画面。没有字幕时先生成/导出字幕再导入。

材料先保存原文，再分段整理：小材料每段最多 12000 字符，超过 120000 字符的长篇每段最多 24000 字符。默认单份预算 1000000 字符，可用 `LINGUALOOP_MAX_MATERIAL_CHARS` 调整到 12000–5000000，超限保留原文并提示。Pro 段落任务采用思考模式 low、16000 tokens，明确截断时最多再以 24000 重试一次；默认同时处理 3 段（`LINGUALOOP_PREPARATION_CONCURRENCY=1–4`）。完成即保存摘要、人物、事件、话题、精确引用和哈希。最后再用全部有序笔记做整书汇总（low、24000 tokens；明确截断时最多以 32000 重试一次），贯通结局、合并人物并准备跨章节话题，最多保留 60 题。网络或汇总失败后重新分析会复用已完成段落。多次模型调用会产生相应费用，取消请求不保证服务停止计费。

单次分析运行总预算默认 1800 秒，可用 `LINGUALOOP_PREPARATION_DEADLINE_SECONDS` 调整；一般非流式调用另有默认 240 秒 wall deadline（`OPENAI_REASONING_DEADLINE_SECONDS`），整书汇总单独默认 600 秒（`OPENAI_SYNTHESIS_DEADLINE_SECONDS`），超时保留完成段落。这些预算不让前台 Flash 等待后台推理。整书汇总成功才允许开聊。话题含开场问题、候选用户意图、回答要点、短回复、追问和原文引用。

前台只调用 Flash。除当前题的预制分支、可用后台资料外，本地按当前发言在已保存的全书准备资料中选择相关情节和人物；不在前台调用 Pro 或搜索整本原文。上下文保留整书概要、最近十条消息与少量早期读者观点，当前改口优先。单条发言上限 4000 字符，Flash 输出上限 160 tokens。证据集中去重，当前发言只传一次。回答简短而具体，不要求每轮提问或变成理解测验。

后台每会话最多准备 12 次、同时最多一个请求、单次任务 45 秒；使用 Pro low、4000 tokens，以当前交流相关的已准备要点、一个引用及最近两条发言生成微型参考。新发言、结束、重置或切换材料会取消旧请求，过期结果丢弃，失败不阻断聊天。新准备必须有非空候选意图、要点及精确引用，无效结构最多尝试两次，明确达到输出预算时不重复相同请求。诊断只含完成原因、tokens、耗时和失败阶段，不保存原始返回或思维链。历史准备在消费前再次校验。自定义话题开聊前，从全部段落及原文按词匹配挑选相关章节、命中附近窗口和均匀全书概览，再交 Pro 整理保存；以后轮次仍只走 Flash。

本阶段提供结束后反馈或关闭反馈；历史 `immediate` 偏好在新讨论中也延后到结束，避免推理纠错阻塞回复。旧 `options=None` 的直接 runner 接口保留兼容语义。`SessionStepResult.timing` 中 `ttft_ms` 是首个可见文本块耗时，`total_ms` 是完整模型回复耗时，不含后续 SQLite 保存；实际端到端耗时应另测。只在回复完整成功后保存用户与助手消息，失败的半段流不进入历史。

默认本地数据保存在平台应用数据目录下的 `LinguaLoop/lingualoop.sqlite3`，可通过 `LINGUALOOP_DATA_DIR` 覆盖。外观与新会话偏好使用 QSettings；凭据保留在本地环境。可选 Kirigami 的兼容性见 [QML runtime](./docs/desktop/QML_RUNTIME.md)。

Windows 默认路径为 `%LOCALAPPDATA%\LinguaLoop\lingualoop.sqlite3`。SQLite 使用 WAL 和按操作连接，保存原文、整理资料、已确认消息、复盘及事件。缓存按原文 SHA256、标题、源语言、学习语言/水平、推理服务/模型和准备版本隔离，不含密钥或文件路径。同一材料重复导入复用原记录和缓存；不完整缓存先展示，再由“继续整理”恢复，不因重新导入自动重复付费分析。完整缓存不被较旧的部分进度覆盖。EPUB 标题优先读取书内元数据。

对话页“历史对话”按当前材料显示全部已保存会话，可恢复旧线程；完成的会话只读。正常重启恢复最近会话并显示对话页。当前草稿在页面/线程切换间保留于内存，未发送草稿不写数据库。数据库及相邻 `-wal`、`-shm` 文件均含本地敏感数据，备份或迁移前先关闭软件。

真实小说验收工具支持持久化接续，必须显式启用真实调用；`build/` 中的数据库含原文和会话，请勿提交：

```powershell
$env:RUN_REAL_AI_TESTS='1'
.venv\Scripts\python.exe scripts/validate_novel.py --real --phase prepare --material 'D:/books/novel.epub' --data-dir build/novel-validation
.venv\Scripts\python.exe scripts/validate_novel.py --real --phase topics --data-dir build/novel-validation
.venv\Scripts\python.exe scripts/validate_novel.py --real --phase start --topic-id topic_ID --data-dir build/novel-validation
.venv\Scripts\python.exe scripts/validate_novel.py --real --phase turn --message 'I read the ending differently.' --data-dir build/novel-validation
.venv\Scripts\python.exe scripts/validate_novel.py --real --phase review --data-dir build/novel-validation
```

`start` 也接受 `--custom-topic`，`turn` 接受 UTF-8 `--message-file`；`export` 输出可读的 `prepared_notes.md`。`chat` 保持一个进程和连接，逐行接收 JSON 命令（`start/turn/wait/state/review/quit`），用于真实连续交谈计时。输出分别包含首字、完整回复和端到端耗时；低于 1 秒是优化目标，结构通过不能代替对话质量与性能结论。

准备完成后，可运行 `scripts/validate_novel_desktop.py --real --data-dir build/novel-validation`。它复制已有数据库到新的 `desktop/` 子目录，以真实模型验证点击选题、键盘输入、发送、切页与草稿保留、不同宽度和复盘，保留本地截图及元数据报告。需要 desktop/dev 依赖和真实调用开关，已有验收副本不会被覆盖。

验证正常软件可用开发探针 `scripts/desktop_session_probe.py --qt-dialogs --output build/native-session`：打开可见 Windows 窗口，使用正常应用数据库，以 Qt 鼠标/键盘事件操作控件，不注入对话记录。stdin 接收 `state/click/type/key/snapshot/quit` JSON 命令，需要保持交互终端。Ctrl+Enter 发送时记录从按键到首段 UI 文本、后续 Qt 帧和完整操作结束的时间，同时保留模型首字/完整回复计时。报告、截图及实际文本仅存 ignored `build/`。默认阻止模型调用；实聊需追加 `--real` 并设置 `RUN_REAL_AI_TESTS=1`。当前结果见[真实小说验收](./docs/planning/NOVEL_ACCEPTANCE_2026-10-28.md)。

## 语音配置与使用

### 可选 LiveKit 本机探针

文本链路验证后，可单独安装官方 RTC/API SDK 做本机传输探针：

```powershell
uv sync --dev --extra desktop --extra realtime
.venv\Scripts\python.exe -m pytest tests\realtime -q
.venv\Scripts\python.exe scripts\probe_livekit.py --download-server
```

探针只使用自写文本和合成 PCM，不读取 AI 凭据或用户学习库。server 固定版本校验后缓存于 ignored `build/livekit-probe/`，只监听 loopback HTTP/UDP，关闭 RTC TCP fallback；临时 token、隐藏子进程与资源均在结束时清理。当前 server 监听/退出已实测。历史空 ICE 列表握手超时；后续空 URL entry 为无效配置，其 ConnectError 不能证明 loopback 不可用。修为合法本机 STUN URL 后，唯一独立差异复验在首 client 连接约 44.9 秒后被总 deadline 取消，底层 RTC 创建状态未观测；仍未证明双参与者音轨和完整语音可用。版本、协议、失败记录与复验命令见 [LiveKit 指南](./docs/desktop/LIVEKIT.md)。基础安装不强制引入 LiveKit，桌面尚未接此 transport。

### 现有分轮语音

复制 `.env.example` 为本地 `.env`，分别配置 `LINGUALOOP_STT_BASE_URL/API_KEY/MODEL`、`LINGUALOOP_TTS_BASE_URL/API_KEY/MODEL/VOICE`。STT 使用 `/audio/transcriptions`，TTS 使用 `/audio/speech` 并请求 PCM WAV；服务需要兼容这些接口。模型和 voice 使用服务实际提供的 ID，文本中转服务不一定提供音频能力。修改配置后重启应用。`--mock` 明确禁用真实语音服务。

选择材料和话题后点击“开始说话”，最多录制 60 秒，点击“结束录音”取得转写。编辑后点击“发送”，AI 回复保存后合成播放。可以重录、停止和重播；识别失败保留当前录音供重试，合成失败只重试合成。详细配置、隐私边界及真人验收步骤见 [分轮语音指南](./docs/desktop/VOICE.md)。

材料会发送给所配置的文本服务，录音会发送给 STT，AI 回复会发送给 TTS。原始录音只作临时处理，数据库保存用户确认发送的文本。正常结束、切换材料或退出时清理临时音频；异常终止的残留见语音指南。
