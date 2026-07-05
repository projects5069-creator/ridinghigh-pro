"""run_stage must grant tools via --allowedTools (TASK-234).

Root cause proven at runtime this session: under
`claude -p --settings <night> --setting-sources local --permission-mode dontAsk`,
the --settings `permissions.allow` list is NOT honored for tool-granting — a
Write to .dancer/plan.md was DENIED despite `Write(.dancer/**)` being in allow.
Adding `--allowedTools "Write"` on the CLI unblocked it, while the --settings
`deny` rules (secret reads) still held (safety-probed). So run_stage must pass an
explicit --allowedTools list mirroring the night allow-set; --settings stays for
deny + hooks, --setting-sources local stays to avoid the CLAUDE.md skill-gate.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SH = (ROOT / "scripts" / "overnight" / "rh-overnight.sh").read_text(encoding="utf-8")


def test_run_stage_passes_allowedtools_flag():
    assert "--allowedTools" in SH, "run_stage's claude call must pass --allowedTools"


def test_rpi_allowed_tools_var_defined_with_core_tools():
    m = re.search(r'RPI_ALLOWED_TOOLS="([^"]*)"', SH)
    assert m, "RPI_ALLOWED_TOOLS must be defined"
    tools = m.group(1)
    for t in ["Read", "Edit", "Write", "Grep", "Glob",
              "Bash(git *)", "Bash(pytest *)", "Bash(uv run *)"]:
        assert t in tools, f"RPI_ALLOWED_TOOLS missing {t!r}"
