# Local build studio

The WebUI uploads NSP/XCI files and keys, inspects content metadata, converts standard XCI files to NSP, and queues native Apple application builds. It runs on `127.0.0.1` with a per-launch browser session. No SQLite, database server, Node build, or queue service is used.

## Start

Use Python 3.11 or newer. Run `scripts/start_webui.command` on macOS, `scripts/start_webui.bat` on Windows, or:

```sh
python3 scripts/start_webui.py
```

Startup does not ask for a data path. It defaults to `.webui-data/` inside the repository (ignored by Git), including uploads, keys, tasks, caches and a local Python environment. Existing compatible Python dependencies are reused without running pip. Missing or incompatible dependencies are automatically installed into `.webui-data/venv`; a completed environment is reused on later launches. The system Python environment is not modified. Python itself must already be installed; first-time dependency setup needs network access.

You may still override the location with `--data-dir` or `NX_DATA_DIR`, including a repository sibling under your home folder. `--tools` selects an existing prepared tools folder. Dependencies and caches follow the chosen data directory.

Open the URL printed by the launcher. The token is exchanged for a local session cookie and removed from the address bar. The service rejects foreign origins and non-loopback hosts. It is a local, single-user tool; do not expose it through a proxy or a public interface. Only one process may use a given data folder.

`start_webui.bat` and `start_webui.command` are launch shortcuts. Set `NX_TOOLS_DIR` to use an external prepared tools folder and its optional `runtime/python.exe` (Windows) or `runtime/bin/python3` (Mac). Otherwise they use system Python. In Spyder, edit the settings at the top of `start_webui.py` and press F5.

## Tools and platforms

Open **Environment & tools** to configure the tools directory and, on Windows, the Apple SDK and Metal compiler paths. Dependency checks report missing files and Python packages. Each check links to the official download or installation instructions; missing entries also show the expected path and a localized setup hint. Missing supported dependencies have an **Install** button; **Install all supported missing dependencies** queues them together. Installation uses the existing serial task queue, `events.jsonl` and `build.log`; view progress, cancel or retry like other tasks. Completed installations trigger a fresh check. Already present dependencies are skipped. Manual entries keep their official instructions. Offline bundle preparation remains available:

```sh
python scripts/prepare_webui_tools.py --out /path/to/external/tools --source-tools /path/to/existing/tools
```

The preparer installs Python dependencies, builds the LibHac extractor, and writes package/license metadata and file SHA-256 hashes. `--wheelhouse` supports offline Python installation; `--python-runtime` includes a separately supplied redistributable Python runtime with its license. Supply a .NET 10 SDK. The preparer does not download or redistribute Apple SDKs, Metal tools, game files, fonts, or keys. Keep third-party tool licenses with a redistributed bundle.

| Host | iOS output | macOS output |
| --- | --- | --- |
| Apple Silicon macOS with the repository's build dependencies | Unsigned IPA | Standalone app ZIP |
| Windows with LLVM/lld, Apple SDK, Metal compiler, .NET and spirv-cross | Offline NVN subset | Unavailable |

Windows uses `scripts/build_ipa_windows.py`. It requires one shader version matching the packaged version and rejects games whose extracted sources require Vulkan, runtime shader capture, Unreal decoding, or Oodle capture. Graphics requirements are detected from the extracted game, not guessed from its name. macOS uses the existing NSP pipeline and its capture support. Application builds require a registered profile and its exact known builds; inspection also works for unregistered titles.

The header language selector switches between Simplified Chinese and English and remembers the choice in this browser. This affects only the WebUI; game language is a separate launch setting. Build-tool logs remain unchanged.

## Windows installation

1. Install [Python 3.11 or newer](https://www.python.org/downloads/windows/) and enable its PATH option. Clone or download this branch, then double-click `scripts/start_webui.bat` or run `python scripts/start_webui.py` from the repository root.
2. Startup installs missing Python dependencies into `.webui-data/venv` and opens the local WebUI. No data-folder prompt or global pip configuration is needed.
3. Open **Environment & tools**, keep the default `.webui-data/tools` directory (or save a different directory), then select **Install all supported missing dependencies**. This downloads the official .NET 10 SDK for the host architecture, verifies its SHA-512 hash, and builds this repository's `nx_extract`. Python build packages can also be installed individually.
4. Install the remaining native tools using the linked official instructions. Keep LLVM `bin` and `lib/clang` together under `tools/ios-cross/toolchain/windows/iphone`; this must include `clang.exe` and `lld.exe`. Put a Windows SPIRV-Cross build at `tools/spirv-cross-build/spirv-cross.exe`. Configure the `metal.exe` path from [Apple Metal Developer Tools](https://developer.apple.com/metal/tools/). Supply an iPhoneOS SDK from your own Xcode installation and save its absolute directory in the SDK field.
5. Select **Recheck**, then upload/import the game packages and keys. Windows produces unsigned iOS packages for the supported offline NVN subset; it cannot produce macOS applications or capture runtime shaders.

## macOS installation

1. Use an Apple Silicon Mac. Install [Python 3.11 or newer](https://www.python.org/downloads/macos/) and [Xcode](https://developer.apple.com/xcode/). Open Xcode once and finish its requested component/license setup. If developer tools point at the standalone Command Line Tools instead of Xcode, choose Xcode in **Xcode > Settings > Locations > Command Line Tools**.
2. Double-click `scripts/start_webui.command`, or run `sh scripts/start_webui.sh` from the repository root. Missing Python dependencies install automatically; data defaults to `.webui-data`.
3. Open **Environment & tools** and install the missing .NET SDK and extractor. The SDK stays in the configured tools directory and does not replace a system installation.
4. With [Homebrew](https://brew.sh/) already installed, the panel can run `brew install xcodegen`, `brew install zstd`, and `brew install spirv-cross`. These use Homebrew's normal installation prefix; the UI identifies this explicitly. Homebrew itself, Xcode and Apple SDKs require manual setup. Standard `/opt/homebrew/bin` and `/usr/local/bin` locations are detected even when launched from Finder.
5. Select **Recheck**, then choose macOS and/or iOS output. Tool presence does not establish shader-chain compatibility; the existing build checks still enforce the repository's tool fingerprints. macOS installation and builds need validation on an actual Mac.

## Python mirror and installer behavior

Startup, WebUI Python installation and the offline bundle preparer default to the [Tsinghua PyPI mirror](https://mirrors.tuna.tsinghua.edu.cn/help/pypi/) at `https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple`. In **Environment & tools**, choose **Official PyPI** and save to switch sources. The saved selection applies to subsequent installs and restarts. The preparer also accepts `--index-url`; `--wheelhouse` bypasses network indexes entirely. This does not change the machine's global pip settings. .NET, Homebrew and NuGet keep their own download sources.

The WebUI does not accept arbitrary commands, package names or download URLs. Installation is serialized with builds. A failed network or package-manager operation remains in the task log and can be retried; successful dependencies are skipped on retry. Cancelling installation stops its process group, but tools already installed remain installed. Xcode, Apple SDKs, Metal tools and Windows LLVM/SPIRV-Cross are manual entries with official links.

## Workflow

1. Upload files, or import existing absolute file paths to avoid another large upload. Chunk uploads resume after reselecting the same file in the same browser. Supply the base game and all profile-required updates.
2. Choose **Build an app**, **Convert XCI to NSP**, or **Inspect game metadata**. For builds, choose iOS and/or macOS and the initial game language, handheld/docked mode, spatial upscaling, and output resolution.
3. Follow the task journal and log. Cancel stops the worker process tree. Downloads are limited to published artifacts. A target failure preserves any successful output from another target.

Language and operating mode apply before game launch. Both app launchers allow changing the defaults and restoring the packaged choices. Spatial upscaling uses Metal 4 FX on supported NVN devices, with ordinary presentation as fallback. It does not add frame generation or force the game's dynamic resolution off. Vulkan output disables the spatial option. Game settings/save data can override the requested language. Device gameplay and scaling quality still require testing on Apple hardware.

XCI conversion validates container bounds, partition hashes, CNMT content membership and content hashes, then streams the original encrypted NCA files into standard NSP containers. Multi-title secure partitions produce separate NSPs. Compressed/split formats are not supported. The converter does not acquire keys or game files.

## Local data and recovery

```
data/
  config.json
  inbox/                  # owned uploads or references to existing files
  tasks/<id>/
    task.json             # immutable request configuration
    events.jsonl          # append-only status/progress journal
    build.log
    inputs/               # normalized inputs and incremental build cache
    outputs/              # downloadable artifacts
```

Restart marks unfinished jobs interrupted; retry is manual. Retry can reuse an existing extraction/shader cache when the original inputs still match. Cache timestamps that differ are checked by SHA-256 before reuse. Build scripts also validate their own fingerprints and shader evidence. Deleting task data is disabled while work is queued/running. Retrying a removed cache performs a fresh build.

Keys are never published as artifacts. Private task copies are removed after completion/cancellation unless explicitly retained. Service-owned uploaded keys are removed when no queued task still needs them; original files imported by path are never deleted. Retaining the task copy enables retry after its uploaded source is removed. Otherwise reimport keys and create a new job. Logs contain file paths and tool output, so keep the data directory private to your OS account.

## Validation

```sh
python -m pip install httpx
python -m unittest discover -s dm/webui/tests -v
python -m dm.webui.tests.integration_nsp --nsp /path/to/game.nsp --keys /path/to/prod.keys --tools /path/to/tools --out /path/to/test-data --build
```

The integration runner exercises the real HTTP task API, metadata inspection, extraction manifest, and optional full build. Results stay on the game drive. IPAs are unsigned; this workflow neither signs nor installs them on a device. macOS packages are ad-hoc signed for local use and need separate Mac validation.

Validated on Windows: Hades II base version 0.0.126424 produced an unsigned IPA with 88 shader keys and 5,418 archive entries. See [the verification summary](webui-hades2-validation.json). The WebUI regression suite includes startup and dependency-help regression tests. Browser checks cover inspection/download links and Chinese/English switching, persistence, and independent game language.
