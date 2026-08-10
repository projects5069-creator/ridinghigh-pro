#!/usr/bin/env bash
#
# check_task_duplicate.sh "<title>" — is this ticket already open?
#
# WHY (2026-08-10): nine tickets were opened in one evening and at least three
# duplicated existing ones — TASK-301 re-opened the root of TASK-259 (the
# once-per-run account snapshot), and TASK-308 re-opened what TASK-54 and
# TASK-286 already cover (skill selection). Nobody was careless; 87 open
# tickets simply cannot be held in a head. This runs in two seconds before
# `backlog task create`.
#
# Scoring: TF-IDF-lite over titles AND bodies. A term's weight is 1/df across
# the open backlog, so a term shared by 60 tickets ("runs", "task") is nearly
# free while a rare one ("snapshot", "skill", "DST") dominates. That is the
# whole trick — plain keyword overlap ranks by common words and finds nothing.
# Title hits count triple: a duplicate usually announces itself in the title.
#
# usage: check_task_duplicate.sh "Single-entry cap leaks between concurrent runs"
#        check_task_duplicate.sh -n 8 "<title>"     (top N, default 5)
# exit 0 = nothing above the threshold · 1 = candidates found (review them)
set -u
REPO="${RH_REPO_DIR:-$HOME/RidingHighPro}"
TOPN=5
while [ $# -gt 0 ]; do
  case "$1" in
    -n) TOPN="$2"; shift 2 ;;
    *) break ;;
  esac
done
[ $# -ge 1 ] || { echo "usage: $(basename "$0") [-n N] \"<כותרת התיק החדש>\""; exit 2; }

/usr/bin/python3 - "$REPO" "$TOPN" "$*" <<'PY'
import os, re, sys, glob, math
from collections import Counter

repo, topn, query = sys.argv[1], int(sys.argv[2]), sys.argv[3]
CLOSED = {"Done", "Archived", "Cancelled"}
STOP = set("""a an and are as at be by for from has have in into is it its of on or that the to
with will not no non can may per via was were this these those which what when where how why
task tasks ticket run runs runing running new fix fixes fixed use used using set sets should
must does do done open close closed one two three each any all more most other others than then
also only just still yet even both same such about after before between during under over
של את על עם אל כל לא זה זו הוא היא הם הן אבל או אם כי כך כדי כמו יש אין רק גם עוד כבר
תיק תיקים משימה משימות""".split())


def fm(t, k):
    m = re.search(rf"^{k}:\s*(.*)$", t, re.M)
    return m.group(1).strip().strip("'\"") if m else ""


def title(t, p):
    m = re.search(r"^title:\s*>-\s*\n((?:[ \t]+\S.*\n)+)", t, re.M)
    if m:
        return " ".join(l.strip() for l in m.group(1).splitlines())
    x = fm(t, "title")
    return x if x and x not in (">-", "|", ">") else os.path.basename(p)


def toks(s):
    s = s.lower()
    s = re.sub(r"[_/\-]", " ", s)
    out = []
    for w in re.findall(r"[a-z0-9֐-׿]+", s):
        if len(w) < 3 or w in STOP or w.isdigit():
            continue
        out.append(w)
    return out


tasks = []
for p in sorted(glob.glob(os.path.join(repo, "backlog/tasks/*.md"))):
    if ".bak" in p:
        continue
    t = open(p, encoding="utf-8", errors="replace").read()
    st = fm(t, "status")
    if not st or st in CLOSED:
        continue
    ttl = title(t, p)
    tasks.append({"id": fm(t, "id"), "title": ttl, "st": st,
                  "tt": set(toks(ttl)), "bt": set(toks(t))})

if not tasks:
    print("אין תיקים פתוchים להשוואה"); sys.exit(0)

df = Counter()
for x in tasks:
    for w in x["bt"]:
        df[w] += 1
N = len(tasks)

q = toks(query)
qs = set(q)
if not qs:
    print("הכותרת לא הניבה מילות-תוכן"); sys.exit(0)

# ⚠️ Two defects measured on the first run (2026-08-10) and fixed here:
#   1. scoring was normalised against the TOP hit, so when the ticket already
#      existed it scored 100% and pushed the real duplicate to 30%. Relative
#      ranking answers "which is most similar", never "is this a duplicate".
#      Now normalised against the query's own maximum attainable score, which
#      is absolute: "how much of my title is already covered by that ticket".
#   2. an identical title matched itself. Harmless in production (the ticket
#      does not exist yet) but it made the tool untestable, and untestable is
#      how a checker rots. Self-matches are skipped by title identity.
def norm(s):
    return re.sub(r"\W+", " ", s.lower()).strip()


qnorm = norm(query)
qmax = 3.0 * sum(math.log(1 + N / df[w]) for w in qs if df.get(w, 0))

scored = []
for x in tasks:
    if norm(x["title"]) == qnorm:      # the ticket itself — not a duplicate of itself
        continue
    s = 0.0
    hits = []
    for w in qs:
        d = df.get(w, 0)
        if d == 0:
            continue
        idf = math.log(1 + N / d)
        if w in x["tt"]:
            s += 3 * idf
            hits.append(w + "*")
        elif w in x["bt"]:
            s += idf
            hits.append(w)
    if s > 0:
        scored.append((100.0 * s / qmax if qmax else 0.0, x, hits))
scored.sort(key=lambda z: -z[0])

THRESH = float(os.environ.get("RH_DUP_THRESHOLD", "12"))
print(f'════ בדיקת-כפילות · "{query[:70]}" ════')
print(f"  הושוו {N} תיקים פתוחים · מילות-תוכן בשאילתה: {len(qs)} · סף התרעה: {THRESH:.0f}%")
print()
if not scored:
    print("✅ אין חפיפה. אפשר לפתוח.")
    sys.exit(0)

for pct, x, hits in scored[:topn]:
    bar = "█" * int(pct / 5)
    print(f"  {pct:5.1f}% {bar:<12} {x['id']:<9} {x['title'][:56]}")
    print(f"         מילים משותפות: {' '.join(sorted(set(hits))[:9])}")
print()
print("  (* = המילה מופיעה גם בכותרת — משקל משולש · האחוז = כמה מהכותרת החדשה כבר מכוסה)")

# ⚠️ Percentage alone cries wolf. Measured 2026-08-10 with a deliberately novel
# title ("espresso machine telemetry to the kitchen dashboard"): TASK-206 scored
# 30% and three more passed 19%, every one of them on a SINGLE generic word
# ("add", "dashboard"). A checker that fires on everything is a checker that
# gets ignored — the exact failure this whole mechanism exists to prevent.
# Alarm therefore needs all three: ≥2 distinct shared terms, at least one of
# them in the TITLE (body-only overlap is weak evidence), and ≥ threshold.
# Calibrated on three cases: 301→259 fires · 308→54/286 listed but does not
# fire (one shared term is genuinely not enough to call it a duplicate) ·
# espresso fires on nothing.
def strong_enough(pct, hits):
    return (pct >= THRESH
            and len({h.rstrip("*") for h in hits}) >= 2
            and any(h.endswith("*") for h in hits))


strong = [z for z in scored if strong_enough(z[0], z[2])]
if strong:
    print()
    print(f"⚠️ {len(strong)} מועמדים חזקים (≥{THRESH:.0f}% · ≥2 מילים · לפחות אחת בכותרת) —")
    print("   קרא אותם לפני שאתה פותח תיק חדש:")
    print("   " + ", ".join(f"{z[1]['id']} ({z[0]:.0f}%)" for z in strong[:8]))
    sys.exit(1)
weak = [z for z in scored[:topn] if z[0] >= THRESH]
if weak:
    print()
    print(f"ℹ️ {len(weak)} חופפים חלקית (מילה משותפת אחת) — הצצה, לא חסימה: "
          + ", ".join(z[1]["id"] for z in weak[:6]))
print("✅ אין מועמד חזק. אפשר לפתוח.")
sys.exit(0)
PY
