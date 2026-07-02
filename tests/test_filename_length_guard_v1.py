"""TASK-133 — filename-length guard (SSoT script scripts/check_filename_length.sh).

Why: a 333-byte backlog basename broke `actions/checkout` on the Linux runner
(ext4 caps a filename component at 255 bytes; Hebrew = 2 B/char), taking CI down
~16h. The guard fails a commit / CI run when any path's basename is >= LIMIT bytes.

These tests exercise the shared check script directly via subprocess:
  - explicit-args mode (used by the pre-commit hook on staged files)
  - the FILENAME_BYTE_LIMIT env override (pre-commit=200 margin, CI=250 hard cap)
  - the boundary (>= is inclusive)
  - no-args mode (used by CI) scanning the real tracked tree
The check measures the basename of the path STRING (no file needs to exist), so
the tests are hermetic and never touch the filesystem's own name limits.
"""

import os
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "scripts", "check_filename_length.sh")


def _run(args, limit=None):
    """Run the guard; return (rc, stdout+stderr). args = list of path strings."""
    env = dict(os.environ)
    if limit is not None:
        env["FILENAME_BYTE_LIMIT"] = str(limit)
    p = subprocess.run(["bash", SCRIPT, *args], cwd=REPO, env=env,
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def _name(nbytes):
    """A path with an ASCII basename of exactly nbytes bytes (under a dir)."""
    return "some/dir/" + ("a" * nbytes) + ""  # 'a'*n -> n bytes


def test_long_basename_rejected_default_limit():
    """A 200-byte basename fails at the default (200) limit -> exit 1 + bytes shown."""
    rc, out = _run([_name(200)])
    assert rc == 1, f"expected reject, got rc={rc}\n{out}"
    assert "200 bytes" in out


def test_normal_basenames_accepted():
    """Ordinary short paths pass -> exit 0, no violation."""
    rc, out = _run(["formulas.py", "backlog/tasks/task-1 - short.md", "a/b/c.txt"])
    assert rc == 0, f"expected accept, got rc={rc}\n{out}"


def test_boundary_is_inclusive():
    """>= LIMIT: exactly 200 rejected, 199 accepted (default limit 200)."""
    rc_at, _ = _run([_name(200)])
    rc_below, _ = _run([_name(199)])
    assert rc_at == 1, "200 bytes must be rejected (>= is inclusive)"
    assert rc_below == 0, "199 bytes must be accepted"


def test_env_limit_override_ci_mode():
    """At the CI limit (250), a 219-byte name passes but a 260-byte name fails."""
    rc_ok, _ = _run([_name(219)], limit=250)
    rc_bad, out = _run([_name(260)], limit=250)
    assert rc_ok == 0, "219 bytes must pass under the 250 CI limit (grandfathered)"
    assert rc_bad == 1 and "260 bytes" in out, "260 bytes must fail under 250"


def test_multiple_paths_reports_each_violation():
    """Two over-limit names -> both reported, exit 1."""
    rc, out = _run([_name(210), "ok/short.py", _name(205)])
    assert rc == 1
    assert "210 bytes" in out and "205 bytes" in out


def test_ci_noargs_scans_tree_and_passes_at_250():
    """CI invocation: no args -> scans git ls-files; the real tree is clean at 250."""
    rc, out = _run([], limit=250)
    assert rc == 0, f"existing tracked tree must pass the 250 CI hard cap\n{out}"


def test_noargs_default_200_flags_grandfathered(tmp_path):
    """No-args (git ls-files) mode flags an over-limit basename at the strict 200 margin.

    Synthetic & hermetic: build a throwaway git repo holding one 210-byte ASCII
    basename, stage it, then run the guard with no args INSIDE that repo. This
    replaces the old dependency on the real tree still carrying grandfathered
    204-219B files — the last such file was shortened (204B->83B, dcd218a), so a
    repo-wide 200 scan of the real tree now finds nothing. What we verify is the
    guard's no-args tree-scan behaviour, not the contents of this repo's tree.
    """
    long_base = "a" * 210  # 210 ASCII bytes, in the old 204-219B grandfathered band
    (tmp_path / long_base).write_text("x")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    env = dict(os.environ)
    env["FILENAME_BYTE_LIMIT"] = "200"
    p = subprocess.run(["bash", SCRIPT], cwd=tmp_path, env=env,
                       capture_output=True, text=True)
    out = p.stdout + p.stderr
    assert p.returncode == 1, f"no-args 200 scan must flag the 210B basename\n{out}"
    assert "210 bytes" in out
