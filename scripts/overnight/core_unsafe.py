"""Single source for the overnight runner's auto-unsafe file set.

The auto-safe filter (triage_filter.py + the layer-2 classifier) and the per-task
diff review all consult THIS module. The unsafe set is defined ONLY in CORE_UNSAFE.txt
next to this file — no facts are duplicated elsewhere (rhpro-live §10 SSoT).
"""
import fnmatch
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
CORE_UNSAFE_FILE = os.path.join(_HERE, "CORE_UNSAFE.txt")


def load_patterns(path=CORE_UNSAFE_FILE):
    """Return the unsafe glob patterns, stripped of comments and blank lines."""
    patterns = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    return patterns


def is_unsafe_path(rel_path, patterns=None):
    """True if rel_path matches any unsafe pattern. fnmatch '*' spans '/', so
    'agent/**' matches 'agent/notifications/email_sender.py'."""
    patterns = load_patterns() if patterns is None else patterns
    p = rel_path.lstrip("./")
    return any(fnmatch.fnmatch(p, pat) for pat in patterns)


def is_unsafe_anchored(path, patterns=None):
    """Like is_unsafe_path, but anchors on every '/'-suffix so absolute and
    worktree-relative paths still match repo-relative patterns. Edit/Write tools
    pass absolute/worktree paths, so '/…/agent/x.py' and '../rh-night-T/agent/x.py'
    must both match 'agent/**'. Over-matching is the SAFE direction (deny → needs_human)."""
    patterns = load_patterns() if patterns is None else patterns
    p = path.replace("\\", "/").lstrip("./")
    parts = [seg for seg in p.split("/") if seg not in ("", ".", "..")]
    for i in range(len(parts)):
        if is_unsafe_path("/".join(parts[i:]), patterns):
            return True
    return False


if __name__ == "__main__":  # `python3 core_unsafe.py [--anchored] <path> [path...]`
    import sys

    args = sys.argv[1:]
    anchored = bool(args) and args[0] == "--anchored"
    if anchored:
        args = args[1:]
    pats = load_patterns()
    check = is_unsafe_anchored if anchored else is_unsafe_path
    for arg in args:
        print(f"{'UNSAFE' if check(arg, pats) else 'safe'}\t{arg}")
