# Local build studio

The WebUI uploads NSP/XCI files and keys, inspects content metadata, converts standard XCI files to NSP, and queues native Apple application builds. It runs on `127.0.0.1` with a per-launch browser session. No SQLite, database server, Node build, or queue service is used.

## Start

Use Python 3.11 or newer and a dedicated data directory on your game drive, outside the repository and your home directory:

```sh
python -m pip install -r dm/webui/requirements.txt
python scripts/start_webui.py --data-dir /Volumes/Games/nxnative-webui
```

Windows example with prepared tools:

```powershell
python scripts/start_webui.py --data-dir D:/Games/nxnative-webui --tools D:/Tools/nxnative
```

Open the URL printed by the launcher. The token is exchanged for a local session cookie and removed from the address bar. The service rejects foreign origins and non-loopback hosts. It is a local, single-user tool; do not expose it through a proxy or a public interface. Only one process may use a given data folder.

`start_webui.bat` and `start_webui.command` are launch shortcuts. Set `NX_TOOLS_DIR` to use an external prepared tools folder and its optional `runtime/python.exe` (Windows) or `runtime/bin/python3` (Mac). Otherwise they use system Python. In Spyder, edit the settings at the top of `start_webui.py` and press F5.

## Tools and platforms

Open **Environment & tools** to configure the tools directory and, on Windows, the Apple SDK and Metal compiler paths. Dependency checks report missing files and Python packages. Each check links to the official download or installation instructions; missing entries also show the expected path and a localized setup hint. Recheck after installing. Downloads and SDK installation are manual. Tool preparation is explicit:

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

Validated on Windows: Hades II base version 0.0.126424 produced an unsigned IPA with 88 shader keys and 5,418 archive entries. See [the verification summary](webui-hades2-validation.json). The WebUI regression suite contains 23 tests. Browser checks cover inspection/download links and Chinese/English switching, persistence, and independent game language.
