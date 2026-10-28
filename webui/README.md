# WebUI package

The WebUI is the fork-owned local build studio. Upstream nxnative code stays at
its original paths; everything here is safe to change without touching upstream.

## Layout

- `server.py`, `jobs.py`, `worker.py`: loopback FastAPI service and serial tasks.
- `capabilities.py`, `dependencies.py`, `apple_tools.py`, `windows_tools.py`:
  environment checks and tool installation.
- `packages.py`, `file_tools.py`: NSP/XCI inspection, XCI conversion and NSZ decompression helpers.
- `repo.py`: repository root, upstream game module import and git exclude helper.
- `staging.py`: materializes the build staging tree (source snapshot + overlays + patches).
- `diffapply.py`: line-ending-normalizing unified-diff applier used by staging and tests.
- `build/windows/`: Windows cross-compile, shader build and IPA packer.
- `overlays/dm/`: fork-only source files copied into the staged `dm/` tree (`DmLauncher.m`, the ObjC port of upstream's iOS launcher).
- `patches/`: ordered upstream hook patches (`series`).
- `launchers/`: canonical Python/PowerShell/shell launchers.
- `tools/`: staging CLI, patch queue, sync check, upstream sync CLI, tool preparation and XCI helper.
- `tests/`: unittest suite (`python -m unittest discover -s webui/tests -t . -v`).

## Build flow

1. The worker calls `staging.ensure()` to create or reuse a stage tree under
   `.webui-data/stage/<key>/tree`.
2. The stage is a full copy of the repository excluding generated/local folders.
   Overlay files are written into `dm/`, then the patch queue is applied with the
   pure-Python applier. The working tree is never modified.
3. The Windows builder runs the staged
   `webui/build/windows/build_ipa_windows.py`; macOS runs the staged
   `scripts/build_ipa_from_nsp.py` with upstream's `--platform mac-app` for the Mac app (zipped
   as `.app.zip`) and the patched launch defaults for iOS. nx_extract is built from the staged, patched C# project.
4. With the optional `--separate-romfs` (WebUI: **Separate IPA and RomFS**,
   default off), the iOS IPA omits `Payload/DmIOS.app/romfs` and
   `webui/build/romfs_archive.py` uses the upstream `pack_ipa.py` to write
   `<ipa>.romfs.zip` with a top-level `romfs/`. The worker verifies both and
   publishes the IPA, archive and their SHA-256 files.
5. Stage reuse is keyed by the source file manifest, platform, patch bytes and
   overlay bytes. `NX_STAGE_REBUILD=1` forces a rebuild; `NX_STAGE_KEEP`
   controls garbage collection.

The Windows shader adapter reads the upstream Metal command lists and preserves
their flags (including `-O1`, invariant positions and iOS relaxed math), replacing
only the tool prefix, target and module cache location. It copies the sources in
the chain's `FILES` manifest and the full-build table generators. SPIRV-Cross uses
the upstream `SPIRV_CROSS` environment override.

Upstream's macOS ARM64 translator assemblies cannot load in Windows x64 .NET.
After checking the pinned upstream DLL hashes, the adapter publishes the current
translator and vendored Ryujinx sources as portable IL in the isolated chain.
The Windows lock records those DLLs and the actual Windows compiler fingerprints;
the repository's translator binaries, lock and chain header stay unchanged.
The first build needs NuGet access; packages are reused from the tools directory's
`nuget` cache (or `NUGET_PACKAGES` when configured).
Recursive translator source copies use Windows extended paths for Python IO;
the longest Ryujinx.Common filenames exceed 260 characters under task folders.
External compiler commands retain ordinary paths.
Cache clearing and task deletion also use extended paths, so those source trees
can be removed through the WebUI without changing Windows system settings.
The generated chain header is published into the build profile for the packer.
Host compilation uses a clang VFS overlay to resolve NVN's quoted chain-header
include to that same file, ahead of the macOS header beside `nvn_mtl.m`, while
leaving the staged upstream sources unchanged.

## Adding an upstream hook

1. Add a patch file to `webui/patches/` and an entry to `series` (patch file and
   repository-relative target).
2. If the hook adds a new source file to an upstream directory, put it under
   `webui/overlays/dm/...` instead and list its target in the overlay allowlist.
3. Add a marker assertion to `tests/test_patch_queue.py`.
4. Run `python webui/tools/sync_check.py` and the full test suite.

See `docs/sync.md` and `docs/webui.md` for the user-facing workflow.

## Launcher interface language

Both iOS launchers offer **Interface language** beside Play: English and Simplified
Chinese. The initial language follows the device language; an explicit choice is
saved immediately in `launcher.uiLanguage` and applies on the next launch too.
This preference controls launcher text only. Game language remains the separate
`DM_LANG` setting, and resetting game settings preserves the interface language.

`localization/launcher.zh-Hans.json` supplies the shared translations. Hook patches
embed them as the optional `uiTranslations` field in `dm/launcher.json` and add the
SwiftUI language picker and translated rows. The ObjC overlay reads the same data.
Unknown text falls back to English. Swift UI patches apply only to Swift stages;
the working tree's upstream files stay untouched.

## Tests

```sh
python -m pip install -r webui/requirements-sync-ci.txt
python -m unittest discover -s webui/tests -t .
```

A module whose package is missing is skipped; `NX_REQUIRE_TEST_DEPS=1` (set in the
sync workflow) turns that into an error. `test_sync_e2e.py` runs the sync tool against a
throwaway upstream and fork, and `test_patched_scripts.py` runs the patched upstream
scripts in a stage; both need `git` / `bash` and skip without them.
