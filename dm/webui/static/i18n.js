// WebUI language is independent of the requested game language. Logs stay verbatim.
const zhMessages = {
"Save settings":"保存设置","Settings saved.":"设置已保存。","Installing ":"正在安装 ","Downloading .NET: ":"正在下载 .NET：",
"Install":"一键安装","Manual setup":"需手动安装","Installs through Homebrew":"通过 Homebrew 安装到其软件目录","install":"安装依赖","Install all supported missing dependencies":"一键安装所有可自动安装的缺失依赖","Python package source":"Python 下载源（保存后生效）","Tsinghua mirror (China)":"清华镜像（国内）","Official PyPI":"PyPI 官方源","Windows installation":"Windows 安装方式","macOS installation":"macOS 安装方式","Homebrew installation instructions":"Homebrew 官方安装说明","Python packages use the Tsinghua mirror by default. Automatic installers run locally and keep logs. Apple SDKs require manual setup.":"Python 默认使用清华镜像源。自动安装在本机执行并记录日志，Apple SDK 需要手动配置。","Install Python 3.11 or newer, then double-click scripts/start_webui.bat. Missing Python packages install automatically. Use this panel to install .NET 10 and build nx_extract. Configure Windows LLVM, SPIRV-Cross, Apple Metal Developer Tools and your iPhoneOS SDK manually. Windows supports iOS packaging only.":"安装 Python 3.11 或更新版本，然后双击 scripts/start_webui.bat，缺失的 Python 依赖会自动安装。在此面板可一键安装 .NET 10 并构建 nx_extract。Windows LLVM、SPIRV-Cross、Apple Metal Developer Tools 和 iPhoneOS SDK 需手动配置。Windows 仅支持打包 iOS 应用。","Install Python 3.11 or newer and Xcode. Open Xcode once to finish its setup, then double-click scripts/start_webui.command or run sh scripts/start_webui.sh. This panel installs .NET 10 and builds nx_extract. With Homebrew already installed, it can also install xcodegen, zstd and spirv-cross. macOS supports macOS and iOS packaging.":"安装 Python 3.11 或更新版本及 Xcode，首次打开 Xcode 完成组件安装。双击 scripts/start_webui.command，或执行 sh scripts/start_webui.sh。在此面板可安装 .NET 10 并构建 nx_extract。已安装 Homebrew 时，还可一键安装 xcodegen、zstd、spirv-cross。macOS 支持打包 macOS 和 iOS 应用。","Dependency installation complete":"依赖安装完成","Wait for queued tasks before installing dependencies.":"请等待当前任务结束后再安装依赖。","Select missing dependencies that support automatic installation":"请选择缺失且支持自动安装的依赖",
  "BUILD STUDIO": "构建工作台",
  "LOCAL WORKSPACE": "本地工作区",
  "Environment & tools": "环境与工具",
  "YOUR GAMES. YOUR HARDWARE.": "你的游戏，你的设备。",
  "From cartridge to": "从游戏文件到",
  "native.": "原生应用。",
  "Convert your game files or build a standalone Apple app.": "转换游戏文件，或构建独立运行的 Apple 应用。",
  "Everything runs on this computer.": "所有处理均在本机完成。",
  "Checking environment…": "正在检查环境…",
  "Bring your files": "添加游戏文件",
  "Choose NSP, XCI & keys": "选择 NSP、XCI 和密钥文件",
  "Base game, required updates and optional DLC": "游戏本体、所需更新和可选 DLC",
  "Files are stored in your local data folder": "上传文件保存在本地数据目录",
  "Or enter an existing local file path": "或输入已有文件的本地路径",
  "Local file path": "本地文件路径",
  "Import": "导入",
  "Choose your output": "选择输出内容",
  "Task": "任务类型",
  "Build an app": "构建应用",
  "Convert XCI to NSP": "XCI 转 NSP",
  "Inspect game metadata": "检查游戏信息",
  "Game": "游戏",
  "Detect from input": "自动识别",
  "Unsigned .ipa": "未签名 .ipa",
  "Standalone .app.zip": "独立应用 .app.zip",
  "Game language": "游戏语言",
  "System": "跟随系统",
  "Simplified Chinese": "简体中文",
  "Traditional Chinese": "繁体中文",
  "English": "英语",
  "Japanese": "日语",
  "Operation mode": "运行模式",
  "Handheld": "掌机模式",
  "Docked": "主机模式",
  "MetalFX spatial upscaling": "MetalFX 空间超分",
  "On": "开启",
  "Off": "关闭",
  "Upscale output": "超分输出分辨率",
  "Auto (screen)": "自动（屏幕）",
  "These are launch defaults. You can change them in the app before starting a game. Game saves may override language.": "这些设置作为应用的启动默认值，也可在启动游戏前调整。游戏存档中的设置可能覆盖语言选项。",
  "Exact registered game versions are required for application builds.": "构建应用需要与已登记配置匹配的游戏版本。",
  "Keep the task's keys copy for reuse": "保留该任务的密钥副本，以便重试",
  "Create task": "创建任务",
  "BUILD JOURNAL": "构建日志",
  "Your tasks": "任务列表",
  "One build at a time · Logs, no database": "串行构建 · 仅使用日志，不使用数据库",
  "No tasks yet. Your next build starts above.": "暂无任务，请在上方创建。",
  "Dependency bundle folder": "依赖工具目录",
  "Windows iPhoneOS SDK": "Windows iPhoneOS SDK 路径",
  "Optional override": "可选，自定义路径",
  "Windows Metal compiler": "Windows Metal 编译器",
  "Path to metal.exe": "metal.exe 的路径",
  "Save paths": "保存路径",
  "Apple tools and SDKs are supplied by you. See docs/webui.md for preparing the offline bundle.": "Apple 工具和 SDK 需自行提供。离线工具包准备方法见 docs/webui.md。",
  "Build log": "构建日志",
  "Close": "关闭",
  "Native execution. Local control.": "原生执行，本地掌控。",
  "Log": "查看日志",
  "Cancel": "取消",
  "Retry": "重试",
  "Delete": "删除",
  "Auto detect": "自动识别",
  "queued": "排队中",
  "running": "运行中",
  "succeeded": "已完成",
  "failed": "失败",
  "cancelled": "已取消",
  "interrupted": "已中断",
  "build": "构建",
  "inspect": "检查",
  "convert": "转换",
  "Waiting": "等待执行",
  "Inspecting package metadata": "正在检查包信息",
  "Extracting code and RomFS manifest": "正在提取代码和 RomFS 清单",
  "Renderer and runtime-capture requirements are checked after extraction.": "解包后会检测图形接口及运行时捕获要求。",
  "Windows requires one shader version matching the package.": "Windows 构建要求着色器版本唯一，并与打包版本一致。",
  "Windows does not support Vulkan builds.": "Windows 暂不支持 Vulkan 构建。",
  "This game needs runtime shader capture on a Mac.": "此游戏需要在 Mac 上捕获运行时着色器。",
  "Application builds require Windows or Apple Silicon macOS.": "应用构建需要 Windows 或 Apple Silicon Mac。",
  "Vulkan game: MetalFX spatial upscaling is unavailable.": "Vulkan 游戏暂不可用 MetalFX 空间超分。",
  "Add exactly one prod.keys file.": "请添加一个 prod.keys 密钥文件。",
  "Select at least one output platform.": "请至少选择一个输出平台。",
  "Delete this task, its copied inputs, cache and outputs? Original imported files remain.": "删除此任务及其输入副本、缓存和输出？通过路径导入的原始文件不会删除。",
  "Tool paths saved.": "工具路径已保存。",
  "Request failed": "请求失败",
  "Add at least one game file": "请至少添加一个游戏文件",
  "Keys upload is incomplete": "密钥文件尚未上传完成",
  "Game input is incomplete": "游戏文件尚未上传完成",
  "Import keys again and create a new task": "请重新导入密钥并创建任务",
  "Task is still active": "任务仍在运行",
  "Wait for tasks before clearing imports": "请等待任务结束后再移除导入文件",
  "Wait for tasks before removing cached inputs": "请等待任务结束后再删除缓存",
  "Wait for queued tasks before changing tools.": "请等待队列中的任务结束后再更改工具路径。",
  "Not enough free space": "磁盘可用空间不足",
  "Choose an existing NSP, XCI or keys file": "请选择已有的 NSP、XCI 或 keys 文件",
  "Expected NSP, XCI or keys": "仅支持 NSP、XCI 或 keys 文件",
  "Open the URL printed by the launcher.": "请打开启动程序输出的完整地址。",
  "Upload not found": "上传记录不存在",
  "missing dependencies": "项依赖缺失",
  "Data folder: ": "数据目录：",
  "Task queued: ": "任务已加入队列：",
  "Remove ": "移除 "
};
Object.assign(zhMessages, {
  "Official instructions": "官方说明",
  "Get / install": "获取 / 安装",
  "Recheck": "重新检测",
  "Environment refreshed.": "环境检测已更新。",
  "Build nx_extract from this repository with scripts/prepare_webui_tools.py; it is not a separate vendor download.": "通过本项目的 scripts/prepare_webui_tools.py 构建 nx_extract，无需单独下载第三方程序。",
  "Get the .NET 10 SDK for your host and place it in the tools/dotnet folder.": "获取适合当前系统的 .NET 10 SDK，并放入工具目录的 dotnet 子目录。",
  "Get host-compatible LLVM with ARM64 and Mach-O support. Keep bin and lib/clang together under tools/ios-cross/toolchain/windows/iphone.": "获取支持 ARM64 和 Mach-O 的本机 LLVM 工具链，将 bin 与 lib/clang 一并保存在 tools/ios-cross/toolchain/windows/iphone 下。",
  "Get lld from the LLVM toolchain. The Windows build uses its Darwin linker mode.": "从 LLVM 工具链获取 lld。Windows 构建使用其 Darwin 链接模式。",
  "Obtain the iPhoneOS SDK from your Xcode installation, then set its directory below. This project does not distribute Apple SDKs.": "从自行安装的 Xcode 获取 iPhoneOS SDK，并在下方指定目录。本项目不分发 Apple SDK。",
  "Get Apple Metal Developer Tools for Windows, then set the metal.exe path below.": "获取 Apple 官方的 Windows Metal Developer Tools，并在下方填写 metal.exe 路径。",
  "Build SPIRV-Cross with its documented CMake instructions and place spirv-cross.exe in tools/spirv-cross-build.": "按照官方 CMake 说明构建 SPIRV-Cross，将 spirv-cross.exe 放入工具目录的 spirv-cross-build 子目录。",
  "Install SPIRV-Cross and add it to PATH. Follow the repository shader-tool lock requirements.": "安装 SPIRV-Cross 并加入 PATH，同时遵循项目着色器工具版本锁定要求。",
  "Install XcodeGen following its official instructions and add xcodegen to PATH.": "按照官方说明安装 XcodeGen，并将 xcodegen 加入 PATH。",
  "Install Zstandard and add zstd to PATH.": "安装 Zstandard，并将 zstd 加入 PATH。",
  "Install Xcode and its command-line tools on the Mac; check the selected developer directory.": "在 Mac 上安装 Xcode 和命令行工具，并检查当前选择的开发工具目录。",
  "Install lz4 into the WebUI Python environment, or rerun scripts/prepare_webui_tools.py for the configured tools folder.": "在 WebUI 使用的 Python 环境中安装 lz4，或对当前工具目录重新运行 scripts/prepare_webui_tools.py。",
  "Install capstone into the WebUI Python environment, or rerun scripts/prepare_webui_tools.py for the configured tools folder.": "在 WebUI 使用的 Python 环境中安装 capstone，或对当前工具目录重新运行 scripts/prepare_webui_tools.py。",
  "Install fonttools into the WebUI Python environment, or rerun scripts/prepare_webui_tools.py for the configured tools folder.": "在 WebUI 使用的 Python 环境中安装 fonttools，或对当前工具目录重新运行 scripts/prepare_webui_tools.py。",
  "Install Pillow into the WebUI Python environment, or rerun scripts/prepare_webui_tools.py for the configured tools folder.": "在 WebUI 使用的 Python 环境中安装 Pillow，或对当前工具目录重新运行 scripts/prepare_webui_tools.py。"
});
let uiLanguage = localStorage.getItem('nx-ui-language') || (navigator.language.startsWith('zh') ? 'zh-CN' : 'en');
if (!['zh-CN', 'en'].includes(uiLanguage)) uiLanguage = 'en';
function t(text) {
  text = String(text ?? '');
  if (uiLanguage !== 'zh-CN') return text;
  if (Object.hasOwn(zhMessages, text)) return zhMessages[text];
  for (const prefix of ['Data folder: ', 'Task queued: ', 'Remove ', 'Installing ', 'Downloading .NET: '])
    if (text.startsWith(prefix)) return zhMessages[prefix] + text.slice(prefix.length);
  return text;
}
const originalText = new WeakMap(), originalAttributes = new WeakMap();
function translateStatic(root = document.body) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const node = walker.currentNode;
    if (node.parentElement.closest('pre,script,style,#ui-language,#inputs,.downloads,#message,.task-title,.task-stage,#host,#data-folder')) continue;
    const source = originalText.get(node) ?? node.textContent;
    originalText.set(node, source);
    node.textContent = source.replace(/\S[\s\S]*\S|\S/, value => t(value));
  }
  for (const element of root.querySelectorAll('[placeholder],[aria-label]')) {
    if (element.closest('#inputs')) continue;
    const source = originalAttributes.get(element) || Object.fromEntries(['placeholder','aria-label'].filter(k => element.hasAttribute(k)).map(k => [k, element.getAttribute(k)]));
    originalAttributes.set(element, source);
    for (const [key, value] of Object.entries(source)) element.setAttribute(key, t(value));
  }
  document.documentElement.lang = uiLanguage;
  document.title = uiLanguage === 'zh-CN' ? 'nxnative · 构建工作台' : 'nxnative · Build studio';
}
