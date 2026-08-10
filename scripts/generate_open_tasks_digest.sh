#!/usr/bin/env bash
#
# generate_open_tasks_digest.sh — "what is sitting on my head", one screen.
#
# WHY (2026-08-10): 87 open tickets, 4,119 lines of body. Nobody can hold that,
# so in practice nobody looks — and the same ticket gets opened twice (301 vs
# 259, 308 vs 54+286, all measured that day). The full bodies stay where they
# are; this is the index you can actually read, regenerated on demand.
#
# Writes docs/OPEN_TASKS_DIGEST.md. Hard ceiling 150 lines: with 87 tickets the
# titles are truncated to fit — **completeness before beauty, never drop a
# ticket to make room.** Age comes from the ticket's own created_date, never
# from file mtime (a touched file is not a young ticket).
#
# Priority rule, so it is reproducible and not a mood:
#   🔴 body names the measurement window (חלון-המדידה / 7/9 / n_ENTER /
#      קפוא עד 4/9) — it can damage data being collected right now
#   🟠 two or more other OPEN tickets reference it, or its body says it
#      blocks/is blocked — work stalls behind it
#   🟡 everything else
set -u
REPO="${RH_REPO_DIR:-$HOME/RidingHighPro}"
OUT="${1:-$REPO/docs/OPEN_TASKS_DIGEST.md}"

/usr/bin/python3 - "$REPO" "$OUT" <<'PY'
import os, re, sys, glob, datetime
from collections import Counter

repo, out = sys.argv[1], sys.argv[2]
TODAY = datetime.date.today()
CLOSED = {"Done", "Archived", "Cancelled"}
MAXLINE, MAXFILE = 120, 150


def fm(t, k):
    m = re.search(rf"^{k}:\s*(.*)$", t, re.M)
    return m.group(1).strip().strip("'\"") if m else ""


def title(t, p):
    m = re.search(r"^title:\s*>-\s*\n((?:[ \t]+\S.*\n)+)", t, re.M)
    if m:
        return " ".join(l.strip() for l in m.group(1).splitlines())
    x = fm(t, "title")
    return x if x and x not in (">-", "|", ">") else os.path.basename(p)


tasks = []
for p in sorted(glob.glob(os.path.join(repo, "backlog/tasks/*.md"))):
    if ".bak" in p:
        continue
    t = open(p, encoding="utf-8", errors="replace").read()
    st = fm(t, "status")
    if not st or st in CLOSED:
        continue
    cr = fm(t, "created_date")[:10]
    try:
        age = (TODAY - datetime.date.fromisoformat(cr)).days
    except Exception:
        age = -1
    n = int(re.sub(r"\D", "", fm(t, "id")) or 0)
    tasks.append({"n": n, "id": fm(t, "id") or f"TASK-{n}", "title": title(t, p),
                  "st": st, "age": age, "text": t, "prio": fm(t, "priority")})

nums = {x["n"] for x in tasks}
indeg = Counter()
for x in tasks:
    for r in {int(m) for m in re.findall(r"TASK-(\d+)", x["text"])} - {x["n"]}:
        if r in nums:
            indeg[r] += 1

WIN = re.compile(r"חלון-המדידה|חלון המדידה|7/9|n_ENTER|קפוא עד 4/9|measurement window")
BLK = re.compile(r"חוסם|נחסם|blocked|blocks |תלוי-סדר|gated on")
GATE = re.compile(r"ייסגר כאשר:|שער-קבלה|שער קבלה|Acceptance Criteria|acceptance gate")

for x in tasks:
    if WIN.search(x["text"]):
        x["p"] = "🔴"
    elif indeg[x["n"]] >= 2 or BLK.search(x["text"]):
        x["p"] = "🟠"
    else:
        x["p"] = "🟡"
    x["gate"] = "✅" if GATE.search(x["text"]) else "❌"
    x["deg"] = indeg[x["n"]]

order = {"🔴": 0, "🟠": 1, "🟡": 2}
tasks.sort(key=lambda x: (order[x["p"]], -x["deg"], -x["age"]))

nogate = [x for x in tasks if x["gate"] == "❌"]
red = [x for x in tasks if x["p"] == "🔴"]
urgent = (red + [x for x in tasks if x["p"] == "🟠"])[:8]

L = []
L.append(f"# מה יושב על הראש — {len(tasks)} תיקים פתוחים")
L.append(f"נוצר {datetime.datetime.now():%Y-%m-%d %H:%M} · `scripts/generate_open_tasks_digest.sh`")
L.append("")
L.append("🔴 מאיים על חלון-המדידה · 🟠 חוסם עבודה אחרת · 🟡 יכול לחכות")
L.append("`שער` = יש קריטריון-סגירה מדיד · `↘N` = כמה תיקים פתוחים מפנים אליו")
L.append("")
L.append(f"## הדחופים ({len(urgent)})")
for x in urgent:
    L.append(f"- {x['p']} **{x['id']}** ({x['age']}d) {x['title'][:70]}")
L.append("")
L.append("## כל התיקים")
for x in tasks:
    ttl = x["title"]
    line = f"{x['id']} | {ttl} | {x['age']}d | {x['p']} | {x['gate']} | ↘{x['deg']}"
    while len(line) > MAXLINE and len(ttl) > 12:
        ttl = ttl[:-4] + "…"
        line = f"{x['id']} | {ttl} | {x['age']}d | {x['p']} | {x['gate']} | ↘{x['deg']}"
    L.append(line)
L.append("")
L.append(f"## חוב: {len(nogate)}/{len(tasks)} תיקים בלי שער-קבלה מדיד "
         f"({100*len(nogate)//max(1,len(tasks))}%)")
# wrap the id list — a single 372-char line was the only thing breaching the
# 120-char rule on the first run (measured 2026-08-10; note macOS awk counts
# BYTES, so it reported 22 breaches where there was one — Hebrew is 2 bytes/char)
row = ""
for x in nogate:
    if len(row) + len(x["id"]) + 1 > MAXLINE:
        L.append(row)
        row = ""
    row += (" " if row else "") + x["id"]
if row:
    L.append(row)

if len(L) > MAXFILE:
    L.append(f"⚠️ הקובץ חרג ({len(L)}>{MAXFILE}) — הכותרות קוצרו, אף תיק לא הושמט.")

with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")

over = [i for i, l in enumerate(L, 1) if len(l) > MAXLINE]
print(f"נכתב {out}")
print(f"  תיקים: {len(tasks)} · שורות: {len(L)} (תקרה {MAXFILE}) · "
      f"שורות מעל {MAXLINE} תווים: {len(over)}")
print(f"  🔴 {sum(1 for x in tasks if x['p']=='🔴')} · "
      f"🟠 {sum(1 for x in tasks if x['p']=='🟠')} · "
      f"🟡 {sum(1 for x in tasks if x['p']=='🟡')} · בלי שער: {len(nogate)}")
sys.exit(0 if len(L) <= MAXFILE else 1)
PY
