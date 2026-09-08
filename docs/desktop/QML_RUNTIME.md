# QML Runtime 运行要求

## Python 依赖

桌面依赖包含 `PySide6`：

```powershell
uv sync --extra desktop
```

Kirigami 不是项目通过 `pip install kirigami` 获取的普通 Python 包。它是 Qt 能发现的 `org.kde.kirigami` QML module，必须和 PySide6 使用兼容的 Qt 主版本。

## Windows 开发

当前入口会优先加载可用的 `org.kde.kirigami`。如果当前环境没有该 module，或 module 与正在运行的 PySide6/Qt 不兼容，POC 会自动加载 `MainFallback.qml`，使用 Qt Quick Controls 验证 Python/QML 业务闭环。这个 fallback 不是最终 Kirigami 视觉效果，但材料、练习、复盘三个页面和 Python ViewModel 是同一套功能边界。

Windows 上，Craft 安装的 Kirigami 原生插件不能直接混用到 PyPI PySide6 wheel 的 Qt 进程中。即使两侧 Qt 都显示为 6.11.1，二进制构建来源不同仍可能在加载 `Kirigamiplugin.dll` 时触发 Windows `0xc0000139`。因此默认 `auto` 模式会拒绝把 `C:\CraftRoot\qml` 的插件加载进 PyPI PySide6，保证桌面端可以稳定使用 fallback 启动。不要通过修改全局 `PATH` 强行将 `C:\CraftRoot\bin` 放在 PySide6 前面。

参考：[Kirigami Windows Setup](https://develop.kde.org/docs/getting-started/kirigami/platforms-windows/)。

### 推荐安装步骤

KDE 官方 Windows 开发文档推荐使用 Craft。建议准备：

- Python 3.12 或 3.13，单独供 Craft 使用；当前项目的 Python 3.14 不建议作为 Craft bootstrap 解释器。
- Visual Studio 2022 的 `Desktop development with C++` 工作负载。
- Windows PowerShell，不要使用 PowerShell ISE。
- Windows Developer Mode，以便 Craft 更快地处理符号链接和解压。

先以普通或管理员 PowerShell 执行 KDE 官方 bootstrap：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
iex ((New-Object Net.WebClient).DownloadString('https://invent.kde.org/packaging/craft/-/raw/master/setup/install_craft.ps1'))
```

安装完成后，使用项目脚本安装 KDE blueprints、Kirigami runtime 并发现 runtime：

```powershell
.\scripts\setup_kirigami_windows.ps1 -InstallRuntime
uv sync --extra desktop
uv run python -c "from lingualoop.desktop.app import kirigami_runtime_available; print(kirigami_runtime_available())"
uv run lingualoop-desktop --mock
```

只检查“进程能创建 Qt 应用、ViewModel 和 QML 页面”而不保持窗口运行时，可以使用：

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
uv run lingualoop-desktop --mock --smoke
```

脚本默认使用 `C:\CraftRoot`，会搜索实际的 `org\kde\kirigami\qmldir` 文件，并把其 import root 写入当前用户的 `QML2_IMPORT_PATH` 和 `QML_IMPORT_PATH`。这一步完成的是 KDE runtime 的安装与发现；要在 Windows 上使用正式 Kirigami 页面，Python binding 和 Qt runtime 也必须来自同一套 Qt 分发。

当前已验证的稳定本地命令是：

```powershell
uv run lingualoop-desktop --mock
```

它会使用 Qt Quick Controls fallback，不会加载不兼容的 Craft DLL。需要检查当前选择的页面时，可以运行：

```powershell
uv run python -c "from lingualoop.desktop.app import kirigami_runtime_available, kirigami_runtime_usable; print(kirigami_runtime_available(), kirigami_runtime_usable())"
```

`True False` 表示 Craft Kirigami 已安装，但当前 PyPI PySide6 不能安全加载它，这是预期保护行为。`LINGUALOOP_KIRIGAMI_MODE=on` 只用于已经确认 Qt/PySide6/Kirigami 来自同一分发的运行环境；不要把它用于目前的 Craft + PyPI PySide6 组合。

如果 Craft 已经创建了 `C:\CraftRoot\craft-tmp`，但脚本提示未安装，说明是 Craft bootstrap 的新目录布局，脚本会自动识别。你的 PySide6 来自 MSVC Qt，因此 Craft 配置必须使用 `windows-cl-msvc2022-x86_64`，不能使用 `windows-gcc-x86_64`。修复已有配置后再安装：

```powershell
.\scripts\setup_kirigami_windows.ps1 -RepairSettings
.\scripts\setup_kirigami_windows.ps1 -InstallRuntime
```

首次安装会先准备 MSYS2、Craft 和 KDE blueprint，可能需要较长时间。若输出
`failed retrieving file ... from mirror.msys2.org`、`Operation too slow` 或
`Craft failed while installing dev-utils/msys-base`，这是下载镜像超时，不代表配置错误。
直接重新执行同一条 `-InstallRuntime` 命令即可，Craft 会复用已经下载和安装成功的缓存；不要
重新改 ABI，也不要删除 `C:\CraftRoot`。如果连续多次失败，再在 MSYS2/Craft 的 mirrorlist
中选择可访问的镜像后重试。

`-RepairSettings` 只修改 `C:\CraftRoot\etc\CraftSettings.ini` 中的 ABI 和 Python 路径，不删除 Craft 文件。它会从 `py -3.12` 自动获取 Python 3.12 的实际安装路径。

如果只想设置已有 Craft runtime 的环境：

```powershell
.\scripts\setup_kirigami_windows.ps1
```

脚本不会提交密钥，也不会修改项目 Python 虚拟环境以外的 LinguaLoop 配置。

## Linux

优先使用发行版提供的与 PySide6/Qt6 匹配的 Kirigami runtime。KDE 官方 Python 教程列出了不同发行版的 `kirigami`、PySide6 和 Qt Quick Controls 依赖。

## Android

Android 是第一优先移动验证目标。先用最小 Kirigami 页面确认 module、QML 资源和 Python 入口都能被打包，再扩大页面范围。普通 pytest 不负责 Android 安装和启动；它们属于环境级验收。

移动模式可用 Qt 官方教程中的环境变量进行本地检查：

```powershell
$env:QT_QUICK_CONTROLS_MOBILE = "1"
uv run lingualoop-desktop --mock
```

本地自动 smoke test 会分别以桌面 `1180x780` 和手机 `360x740`、`412x915` 尺寸加载 QML。它验证页面可创建、可调整尺寸且不会依赖真实 API；不等价于 Android 包已经构建或真机已运行。

## 资源打包

QML 文件通过 `setuptools.package-data` 随 `lingualoop.desktop` 分发。发布前仍需增加平台打包配置，确保 `org.kde.kirigami`、Qt Quick Controls style 和图标资源一起进入安装包。
