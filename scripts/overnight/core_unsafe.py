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


if __name__ == "__main__":  # tiny CLI: `python3 core_unsafe.py <path> [path...]`
    import sys

    pats = load_patterns()
    for arg in sys.argv[1:]:
        verdict = "UNSAFE" if is_unsafe_path(arg, pats) else "safe"
        print(f"{verdict}\t{arg}")
