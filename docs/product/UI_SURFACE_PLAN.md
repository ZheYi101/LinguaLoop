# LinguaLoop MD3 页面方案

本地资料增量（2026-10-28）：对话页新增“历史对话”，按当前材料列出标题、首条读者发言、轮数和日期；选择历史恢复原线程，完成会话只读。重启有会话时直接展示对话页，切换线程保留未发送草稿于内存。材料按 ID 选中，重复导入复用缓存，完整结果显示“检查整理”，部分结果显示“继续整理”。未配置 AI 时也能查看本地库，不生成模拟回复。图标路径已在可见 Windows 窗口检查，标题栏继续使用应用内控件。

2026-10-28 真实长篇检查：材料摘要默认最多七行并可展开，避免逐段笔记把整理状态和开聊入口推到长页面底部；未完成整书汇总时明确显示继续入口并禁止开聊。余额不足显示 HTTP 402 的明确恢复提示。完整小说资料的五档尺寸检查属于只读渲染，真实模型对话仍需另外验收。

本轮主线：导入已沉浸内容 → 整理成可复用的讨论材料 → 选择或自定话题 → 流式文本讨论 → 轻量复盘。语音仍是产品长期目标；当前阶段优先验收文本、双模型分工与响应时间，STT/TTS 不作为开聊前提。权威状态与证据总表见 [ROADMAP](../planning/ROADMAP.md)。

## 设计参考与边界

继续使用现有 PySide6/QML 和 Material Design 3。已实际核对两个参考仓库的主分支源码：

- [Hoshi MainShellUi.kt（b08acc09）](https://github.com/HuangAntimony/Hoshi-Reader-Android/blob/b08acc09a87c532564fa1139cbd5efae57923259/app/src/main/java/moe/antimony/hoshi/features/bookshelf/MainShellUi.kt) 与同目录 `BookshelfView.kt`：采用内容优先的自适应 rail / bottom bar、受约束的内容宽度和网格留白层级。
- [Fushi 自绘桌面标题栏（98710dc9）](https://github.com/hajisensai/Fushi/blob/98710dc9cfddb5355872df7c662e61216626ae93/fushi/lib/src/utils/components/fushi_desktop_title_bar.dart)：参考应用主题与窗框连续、避免重复标题、保留桌面窗口操作的思路。

两者为 GPL 项目。本轮仅参考交互与层级，未复制代码、图片、字体、图标或其他资产。LinguaLoop 保留自己的品牌、QML 组件与 Material Symbols 图标许可证。

## 主题与应用壳

`design/AppTheme.qml` 集中定义紫色种子 `#6750A4` 的浅色 / 深色语义色彩、字号、间距、形状与约 200ms 动效。支持跟随系统和减少动效。中文优先系统中文字体，日语正文优先 Yu Gothic UI；离屏验证显式加载字体。`MLabel` 强制纯文本。

默认 Qt ApplicationWindow 加 `Qt.FramelessWindowHint`，由项目绘制 56px 同色顶栏，替换 Windows 原生标题栏。标题栏支持拖动、双击最大化/恢复、最小化、最大化/恢复及关闭；四边与四角将缩放操作交给 Qt `startSystemResize`，不自行计算屏幕像素。窗口尺寸与位置使用独立 QSettings 保存，恢复时限制在可用屏幕内，避免拔掉显示器后失联。

主入口只有“材料”“对话”。复盘、设置保留在宽窗口侧栏底部与顶部“更多”菜单。紧凑窗口底栏仅保留两个主入口；顶部“更多”仍可进入次级页面。键盘支持 Ctrl+1 / Ctrl+2 导航、Ctrl+, 设置、Ctrl+Enter 发送、Alt+F10 最大化/恢复、Alt+F4 关闭。

| 窗口宽度（Qt 逻辑像素） | 布局 |
| --- | --- |
| <600 | 单列、双入口底栏，16px 页面边距 |
| 600–1199 | 80px rail 与主内容，24px 边距 |
| ≥1200 | rail 与主内容；对话另显示 320px 语境面板 |

窄窗口用“查看本次语境”展开 Dialog。页面持续存在，导航和窗口尺寸切换保留草稿。最小窗口 360×560，长对话和输入区可滚动。交互控件至少 48×48；操作系统窗口缩放边缘使用 6px 命中区域。一般文字对比度目标 4.5:1，焦点、禁用、悬停和按下状态统一处理。

## 材料与话题

材料页提供导入、粘贴和材料切换。格式为 TXT、Markdown、DOCX、SRT、VTT、EPUB、XLSX；视频仅分析同目录同名 SRT/VTT 字幕，不声称理解画面。先保存原文，再由推理模型分段整理。页面显示真实整理状态、摘要及按需展开的大纲和人物；失败后可继续整理。

话题完整保留，不再截断成三个。按类别筛选、标题/开场问题搜索；宽内容区域使用双列卡片，窄窗口单列。各话题默认只展示标题、类别、开场问题和选择操作，点击“参考”才展开源文依据、可能的用户回应方向、回答要点与示例。预测仅是讨论参考，不计作用户事实。

自定义话题与 roleplay 配置按需展开。用户选好话题即可开始；自定义话题开始时明确显示“正在整理自定义话题”，等待推理模型准备并保存后再进入正常讨论。未完整整理的材料不能伪装成已就绪。

## 文本讨论与次级能力

对话页主体留给消息。文本发送为当前主操作，未配置语音时不显示录音按钮及“语音未配置”的阻碍提示；配置齐全时仍可使用原有分轮语音能力，设置页保留独立服务状态。

`send_message(..., on_delta=...)` 的 worker 线程 delta 经 Qt queued signal 更新临时回复气泡。完成后用确认后的消息替换临时气泡并写入本地历史；失败保留草稿，临时流式文字不冒充已保存的回复。重复提交被禁用，失败重试清空上一轮临时文本。

页面显示实际“首字耗时”和“完整回复耗时”，区分模型调用时长，不承诺已经小于 1 秒。独立轮询后台准备状态，显示正在准备、准备就绪或暂不可用；后台准备不阻断前台发送。当前设置只提供结束后反馈 / 关闭，旧即时反馈偏好明确提示本阶段延后到结束。

复盘仍保留总结、最多三个默认展开重点、复习队列、评级和导出。设置保留主题、语言、反馈、设备、服务状态和本地数据操作。密钥只读本地环境，不写入学习数据库。

## 本轮 UI 验证记录（2026-10-24）

- Mock / Qt Test：实际选择话题、分类、搜索、展开参考、键盘输入自定义话题、Ctrl+Enter 发送、观察中间流式文字与确认后的消息、响应计时、后台准备、失败重试、三轮模拟语音回归、复盘、重启恢复。
- 布局与可访问性：明暗 / 系统主题，360、600、800、1180、1440px；中日长文本、草稿保留、焦点、按钮边界和发送按钮配对颜色对比度。
- 窗口控制：offscreen 检查 frameless flags、八个缩放句柄、点击最小化 / 最大化 / 恢复 / 关闭、Alt+F10、次级入口，移除显示器坐标恢复与原生调用转交。
- Windows 真实平台隐藏窗口：`scripts/check_desktop_window.py` 得到 `platform=windows, visible=false, win32_style=0x860b0000, native_caption=false, device_pixel_ratio=1.0`。只证明 HWND 样式中没有原生标题栏；未显示窗口。
- 预览：`scripts/render_ui_preview.py` 使用独立临时 SQLite / QSettings 与 Mock provider，不读取用户数据库或 `.env`，输出 `build/ui-preview/`。`material-topics.png` 展示话题网格，`streaming.png` 展示真实异步 mock delta 更新，另有浅深色及窄窗口截图。

UI 负责人本地复验：`RUN_REAL_AI_TESTS=0` 下运行 `python -m pytest tests/test_desktop_workflow.py tests/test_desktop_imports.py tests/test_desktop_native_window.py -q`，结果 **16 passed in 19.48s**。这是 Mock / Qt 与隐藏 HWND 证据，不是 DeepSeek 真实请求或语音验收。

历史分发验证：`uv build --wheel --out-dir build/package-check` 成功；`python scripts/check_wheel_resources.py build/package-check/lingualoop-0.1.0-py3-none-any.whl` 验证 **39 个 QML / SVG / license 资源完整**，从隔离临时目录导入 wheel 内的 `WindowController`，以临时 SQLite / QSettings 和隐藏窗口加载全部 QML，核对 frameless flags、窗口按钮、拖动区与缩放句柄。该历史候选 SHA256 为 `D05017B125D0AB515A0EFE9D920795D1B9B073876978FC48FF238F892A413449`，后被下述固定状态区修复替代，不能作为最终候选。未安装到用户全局环境、未发布。增强探针首次通过 QObject ownership 树查 Repeater 句柄失败，改用 QQuickItem 视觉树遍历后通过；wheel 内容及应用源码未因此更改。最终包身份与独立分发验收以 ROADMAP / TEXT_ACCEPTANCE 为准。

首次 QML 失败是 `AbstractButton.action` FINAL 属性冲突，组件字段更名为 `glyph` 后通过。首次新增键盘测试误用了只支持 QWidget 的 `keyClicks`，随后传入整数又命中字符重载而插入大写；最终使用显式 `Qt.Key` 逐键事件，并保留精确草稿断言。导航快捷键在 offscreen 焦点下增加 `ApplicationShortcut` 上下文，单项复验通过。这些失败已修复，不代表真实服务已验收。

最终回归追加：独立全仓最初出现分类点击后仍显示 12/12 的失败。加强命中诊断后证实分类中心相对材料 viewport 为 `(143, -99)`，位于视口上方；旧夹具只检查全窗口范围，滚动采用未完成布局的坐标而误点标题区域。夹具现对实时布局校准滚动位置、确认在 viewport 内，hover 后重新定位中心，并验证实际 `mousePress` 的 `down` 状态后松开；只点击一次，分类数量和精确自定义草稿断言保留。按住分类时触发材料轮询的回归未发现按钮失效，不能把原失败归因于轮询重建。

同轮严格诊断另捕获真实布局问题：后台准备状态首次出现令录音按钮从 `(188, 739)` 移至 `(188, 702)`，上移 37px。对话输入区现保留固定 40px 的两行状态空间，后台准备和计时更新不再改变发送 / 录音命中区域；新增 idle → ready + timing 前后按钮坐标保持不变的断言。修复后 `python -m pytest tests/test_desktop_workflow.py -q` **9 passed in 16.83s**；页面源码至此冻结，待独立全仓和最终 wheel 复验。截图已按冻结版本刷新，仍仅使用 Mock。

尚未覆盖：物理鼠标拖动、Windows Snap 行为、跨 DPI / 多显示器实际移动、真实云端语音和 LiveKit 连续通话。Qt Test 与隐藏 HWND 检查不能替代这些目标环境验收。全套最终测试数量以 ROADMAP 独立验收记录为准。
