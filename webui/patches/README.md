# Upstream hook patches

These patches keep fork behavior out of the upstream working tree. They are
applied only to the staging tree created by `webui/staging.py`.

- Fork base: `233f18f421344fcd3b61559459ef8649d6c38a54`
- Fork reference: `a8bfd0ddac3a976b770e05db64f3932d29772ce8`
- Patches were generated with
  `git diff --no-ext-diff --unified=3 233f18f -- <target>`.
- `series` lists the patch file and its target. The applier rejects a target
  that differs from the series entry or escapes the tree.
- Patch files are LF. The source checkout uses CRLF; `webui/diffapply.py`
  normalizes both sides and writes LF into the stage.

## Patch 0009 corrections

The fork's `scripts/build_ipa_from_nsp.py` imported `json` only inside
`Progress.stage`, while the WebUI launch-defaults block calls `json.loads`
at module level. Patch 0009 adds a top-level `import json`. It also points the
macOS target at the moved `webui/build/macos/pack_app.py`.

## Do not regenerate

`.gitignore`, `README.md` and `dm/ios/project.yml` are not part of the patch
queue. The first two are restored to upstream; `project.yml` is the single
intentional direct edit (fullscreen launch keys).

After an upstream sync, port the hooks onto a temporary hooks branch and run
`python webui/tools/patch_queue.py regenerate`. See `webui/docs/sync.md`.
