# nxnative fork: WebUI and Windows build support

This repository is a fork of [seedds/nxnative](https://github.com/seedds/nxnative).
Upstream code lives at its original paths (`dm/`, `scripts/`, `docs/`, `README.md`)
and is kept clean so that upstream can be fetched and merged without carrying fork
changes in every file.

All fork-owned code lives under `webui/`:

| Path | Purpose |
|---|---|
| `webui/` | Local build studio (FastAPI), task queue, launchers, tool preparation |
| `webui/build/windows/` | Windows iOS cross-compile, shader build and IPA packer |
| `webui/build/macos/` | macOS application wrapper and packager |
| `webui/overlays/dm/` | Fork-only source files placed into the staged `dm/` tree |
| `webui/patches/` | Upstream hook patches applied only to the build staging tree |
| `webui/launchers/` | Canonical launchers (thin wrappers are at the repository root) |
| `webui/tools/` | Staging, patch queue, sync checks and helper CLIs |
| `webui/docs/` | WebUI guide, plan, validation data and upstream sync notes |

## Start

Windows: double-click `start-webui.bat` (or `webui\launchers\start_webui.bat`).
macOS: double-click `start-webui.command` (or run `webui/launchers/start_webui.sh`).

The launchers keep their data in the repository's `.webui-data/` directory. That
directory is local-only and is added to `.git/info/exclude`; the upstream
`.gitignore` is not modified.

## Builds use a stage

A build never writes into the upstream working tree. `webui/staging.py` copies
the repository into `.webui-data/stage/<key>/tree`, applies the six overlays and
the nine patches under `webui/patches/`, and runs the build from that copy. The
stage is reused until a source file or patch changes.

The only intentional direct edit to an upstream file is `dm/ios/project.yml`,
which declares the iOS fullscreen launch configuration (`UIRequiresFullScreen`
and `UILaunchScreen`). Everything else is a patch or an overlay.

## Upstream sync

The upstream remote is `https://github.com/seedds/nxnative.git`. The current
fork baseline is `233f18f`; upstream has diverged since then. Do not merge
upstream blindly: follow `webui/docs/sync.md`, port the hook patches onto the
new upstream tree and refresh `webui/patches/`. `webui/tools/sync_check.py`
reports upstream-owned edits and patch applicability.

See `webui/README.md` for the developer overview.
