---
id: TASK-157
title: >-
  Fix dead clipboard auto-copy: cc-copy-last Stop hook killed by modern-python
  python3 shim; harden last-assistant-text parse
status: Done
assignee: []
created_date: '2026-06-11 13:45'
updated_date: '2026-06-11 15:09'
labels:
  - tooling
dependencies: []
priority: medium
ordinal: 160000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
ROOT CAUSE (verified 2026-06-11, CLI 2.1.170): The Stop hook $HOME/bin/cc-copy-last (registered in ~/.claude/settings.json) auto-copies the assistant's last response to the macOS clipboard, but is DEAD since 2026-06-09. (1) SHIM: its shebang is #!/usr/bin/env python3, and PATH python3 now resolves to the modern-python plugin shim (.../trailofbits/modern-python/1.5.0/hooks/shims/python3) which exits 1 demanding 'uv run python3' -> hook dies before pbcopy. Evidence: /tmp/cc-copy-last.log frozen at 2026-06-09 09:25 (2 entries), zero copies since; manual run via /usr/bin/python3 exits 0. (2) FRAGILE PARSE: logic collects assistant text AFTER the last type==user line, but CC records tool_result as type==user, so final assistant text can be missed (returns empty). pbcopy itself works (PBCOPY_TEST_OK verified). This makes the stale memory 'Stop hook sandboxed' inaccurate — cause is the shim, not a sandbox. Separately, when Amihay pastes ~/bin/rh-run 'CMD' as a prompt, Claude runs Bash(inner CMD) not the wrapper, so rh-run's own pbcopy never fires; fixing the Stop hook makes this irrelevant (auto-copy captures the whole response regardless). PROPOSED FIX (do NOT implement until chosen): make cc-copy-last shim-immune (rewrite in bash+jq, or shebang to a non-shim interpreter) AND harden parse to walk backward and grab trailing contiguous assistant text blocks. Then one-time verify via Cmd+V. Touches tooling only - no trading code / PK.
<!-- SECTION:DESCRIPTION:END -->
