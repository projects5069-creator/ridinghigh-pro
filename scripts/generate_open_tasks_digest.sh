#!/usr/bin/env bash
#
# generate_open_tasks_digest.sh — "what is sitting on my head", one screen.
#
# WHY (2026-08-10): 87 open tickets, 4,119 lines of body. Nobody can hold that,
# so in practice nobody looks — and the same ticket gets opened twice (301 vs
# 259, 308 vs 54+286, all measured that day). The full bodies stay where they
# are; this is the index you can actually read, regenerated on demand.
#
# Writes docs/OPEN_TASKS_DIGEST.md. Age comes from the ticket's own created_date,
# never from file mtime (a touched file is not a young ticket).
#
# MERGED 2026-08-10: this file used to be one of TWO task lists — the short index
# here, and a hand-written "what it means / what to do" per ticket that lived
# outside the repo. Two lists means two truths, so the explanations moved in as
# docs/TASK_EXPLANATIONS.md and are joined here by ticket number.
#
# ⚠️ THE 150-LINE CEILING IS GONE, DELIBERATELY. Three lines per ticket over ~90
# open tickets cannot fit in 150 and no arithmetic makes it fit. The rule that
# survives is the one that always mattered: **completeness before beauty, never
# drop a ticket to make room.** The ceiling is now derived from the ticket count
# instead of being a constant, so it still fails loudly if the file bloats for
# any OTHER reason.
#
# ⚠️ The explanations are AUTHORED, not derived — written by reading 88 full
# bodies. No script can regenerate them. A ticket with no entry is marked
# explicitly as missing rather than silently skipped.
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
MAXLINE = 120
EXPL = os.path.join(repo, "docs/TASK_EXPLANATIONS.md")


def fm(t, k):
    m = re.search(rf"^{k}:\s*(.*)$", t, re.M)
    return m.group(1).strip().strip("'\"") if m else ""


def title(t, p):
    m = re.search(r"^title:\s*>-\s*\n((?:[ \t]+\S.*\n)+)", t, re.M)
    if m:
        return " ".join(l.strip() for l in m.group(1).splitlines())
    x = fm(t, "title")
    return x if x and x not in (">-", "|", ">") else os.path.basename(p)


# ── authored explanations, joined by ticket number ────────────────────────
# Two fields per ticket: what it means, what to do. Anything else in that file
# (status, evidence) is deliberately NOT pulled in — the digest is an index, and
# status already lives in the ticket itself.
expl = {}
if os.path.exists(EXPL):
    blocks = re.split(r"\n(?=## TASK-)", open(EXPL, encoding="utf-8").read())
    for b in blocks:
        m = re.match(r"## TASK-(\d+)", b)
        if not m:
            continue
        def grab(label):
            g = re.search(rf"\*\*{label}:\*\*\s*(.+)", b)
            return g.group(1).strip() if g else ""
        expl[int(m.group(1))] = (grab("מה זה אומר"), grab("מה צריך לעשות"))

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

WIN = re.compile(r"חלון-המדידה|חלון המדידה|7/9|n_ENTER|measurement window")
BLK = re.compile(r"חוסם|נחסם|blocked|blocks |תלוי-סדר|gated on")
GATE = re.compile(r"ייסגר כאשר:|שער-קבלה|שער קבלה|Acceptance Criteria|acceptance gate")
# ⚠️ 2026-08-10, second pass. The first version collapsed "touches the
# measurement window" and "needs attention now" into one 🔴, so TASK-276 and
# TASK-279 — both ruled explicitly to land AFTER 2026-09-04 — sat at the top of
# the urgent list. A list that shows you what you cannot act on is a list you
# stop reading. Urgency and window-state are now two independent fields.
# ⚠️ the first cut of this regex missed TASK-279 for two independent reasons,
# both measured 2026-08-10: it states its constraint in ISO form ("after
# 2026-09-04 only"), and its Hebrew phrasing wrapped across a line break
# ("…אלא אחרי\n4/9…"). Hence \s+ instead of a literal space, and the ISO date.
FROZEN = re.compile(r"אחרי[\s-]+4/9|קפוא עד[\s-]+4/9|לא לפני[\s-]+4/9|נכנסת אחרי"
                    r"|after\s+4/9|after\s+2026-09-04|2026-09-04 only|frozen until")
LATE = re.compile(r"1/11|2026-11-01|November|נובמבר|15/8|שבת 15/8|בחורף|אוקטובר")

for x in tasks:
    frozen = bool(FROZEN.search(x["text"]))
    late = bool(LATE.search(x["text"]))
    x["w"] = "🧊" if frozen else ("⏳" if late else "  ")
    if frozen:                                   # ruled for after the window
        x["p"] = "🟡"
    elif WIN.search(x["text"]):
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
# a frozen ticket is never urgent — that is the whole point of the split
urgent = [x for x in (red + [y for y in tasks if y["p"] == "🟠"]) if x["w"] != "🧊"][:8]

L = []
L.append(f"# מה יושב על הראש — {len(tasks)} תיקים פתוחים")
L.append(f"נוצר {datetime.datetime.now():%Y-%m-%d %H:%M} · `scripts/generate_open_tasks_digest.sh`")
L.append("")
L.append("**דחיפות:** 🔴 עכשיו · 🟠 חוסם עבודה אחרת · 🟡 יכול לחכות")
L.append("**חלון:** 🧊 הוכרע לאחרי 4/9 · ⏳ דדליין מאוחר (נוב׳/אוק׳/15.8) · ריק = ללא")
L.append("`שער` = יש קריטריון-סגירה מדיד · `↘N` = כמה תיקים פתוחים מפנים אליו")
L.append("⚠️ תיק 🧊 לעולם אינו ברשימת-הדחופים, גם אם גופו נוקב בחלון-המדידה.")
L.append("")
L.append(f"## הדחופים ({len(urgent)})")
for x in urgent:
    L.append(f"- {x['p']}{x['w'].strip()} **{x['id']}** ({x['age']}d) {x['title'][:68]}")
L.append("")
L.append(f"## קפואים לאחרי 4/9 ({sum(1 for x in tasks if x['w']=='🧊')})")
L.append(" ".join(x["id"] for x in tasks if x["w"] == "🧊") or "—")
L.append("")
L.append("## כל התיקים")
L.append("")
missing_expl = []
for x in tasks:
    ttl = x["title"]
    def mk(t):
        return f"{x['id']} | {t} | {x['age']}d | {x['p']} | {x['w']} | {x['gate']} | ↘{x['deg']}"
    line = mk(ttl)
    while len(line) > MAXLINE and len(ttl) > 12:
        ttl = ttl[:-4] + "…"
        line = mk(ttl)
    L.append(line)
    m, d = expl.get(x["n"], ("", ""))
    if m or d:
        # wrap prose so the 120-char rule keeps holding — it was written for the
        # table rows, and adding un-wrapped prose would have quietly broken it
        # on 64 lines (measured 2026-08-10 on the first run of the merged format)
        def emit(label, body):
            words, row = body.split(), f"  · **{label}:**"
            for w in words:
                if len(row) + 1 + len(w) > MAXLINE:
                    L.append(row)
                    row = "    "
                row += (" " if row.strip() else "") + w
            if row.strip():
                L.append(row)
        if m:
            emit("מה זה אומר", m)
        if d:
            emit("מה צריך לעשות", d)
    else:
        missing_expl.append(x["id"])
        L.append("  · ⚠️ **אין הסבר** — נכתב ביד, לא נגזר. להוסיף ל-docs/TASK_EXPLANATIONS.md")
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

# derived, not constant. Budget per ticket: 1 table row + up to 3 wrapped lines
# of "what it means" + up to 3 of "what to do" + 1 blank ~= 7. Measured on the
# first merged run: 450 lines for 89 tickets = 4.6/ticket, so 7 leaves real
# headroom and still fires if the file bloats for some other reason.
MAXFILE = 7 * len(tasks) + 60
if missing_expl:
    L.append("")
    L.append(f"## ⚠️ בלי הסבר ({len(missing_expl)}) — נכתב ביד, אינו נגזר")
    L.append(" ".join(missing_expl))
if len(L) > MAXFILE:
    L.append(f"⚠️ הקובץ חרג ({len(L)}>{MAXFILE}) — אף תיק לא הושמט.")

with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")

over = [i for i, l in enumerate(L, 1) if len(l) > MAXLINE]
print(f"נכתב {out}")
print(f"  תיקים: {len(tasks)} · שורות: {len(L)} (תקרה {MAXFILE}) · "
      f"שורות מעל {MAXLINE} תווים: {len(over)}")
print(f"  בלי הסבר: {len(missing_expl)}")
print(f"  🔴 {sum(1 for x in tasks if x['p']=='🔴')} · "
      f"🟠 {sum(1 for x in tasks if x['p']=='🟠')} · "
      f"🟡 {sum(1 for x in tasks if x['p']=='🟡')} · בלי שער: {len(nogate)}")
sys.exit(0 if len(L) <= MAXFILE else 1)
PY
