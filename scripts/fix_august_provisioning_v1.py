#!/usr/bin/env python3
"""
fix_august_provisioning_v1.py — TASK-242
────────────────────────────────────────
One-shot repair for the 2026-08 provisioning split (deadline: rotation 1/8 05:01 UTC).

Verified state that motivated this script (2026-07-29, read-only Drive audit):
  • sheets_config["2026-08"] held 9/25 tabs — the 16 AGENT_SHEET_NAMES were missing.
  • All 9 core August sheets sat under BAD_AUG (2026-08 inside RidingHigh-Data),
    not under CANON_AUG (2026-08 inside the canonical RidingHighPro root).
  • Those 9 sheets carried only 2 permissions (owner + the shared SA). The three
    dedicated service accounts (_AS / _AM / _HA) were absent, so from 1/8 auto_scan
    would have hit 403 on every core tab.

Root cause (do NOT "fix" it here): sheets_manager._get_root_folder_id resolves
ROOT_FOLDER_ID through the SHARED service account, which genuinely has no
permission on the canonical root, so the 404 is real and the RidingHigh-Data
fallback is formally correct. This script therefore authenticates ONLY via
sheets_manager._get_drive_service_oauth() and never calls _get_root_folder_id.

Scope guard: touches 2026-08 only. Never deletes anything, never removes a
permission, never writes to any other month.

Usage:
    python3 scripts/fix_august_provisioning_v1.py --audit
    python3 scripts/fix_august_provisioning_v1.py --move            # dry-run
    python3 scripts/fix_august_provisioning_v1.py --move --apply
    python3 scripts/fix_august_provisioning_v1.py --reshare         # dry-run
    python3 scripts/fix_august_provisioning_v1.py --reshare --apply

--dry-run is the default; nothing is written without --apply.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sheets_manager  # noqa: E402

DEFAULT_MONTH = "2026-08"

CANON_ROOT = "1mHSdsTENVuMTtlv4XM54SrbadCEF_HHh"
CANON_AUG = "1k-N29HSIX13KHAgyg4qXZ6H6V_KcS0RQ"
BAD_AUG = "1S5bAu4ppxscJE8X-FbtT2BGxs7-_nyR8"

# Set by main() from --month / the resolved canonical month folder. Every command
# reads these instead of the 2026-08 constants, so the tool works for any month
# while the audited August ids stay documented above.
MONTH = DEFAULT_MONTH
TARGET_FOLDER = CANON_AUG

SHARED_SA = sheets_manager.SERVICE_ACCOUNT_EMAIL

# Every identity a 2026-08 sheet must carry, with the role it actually needs.
# The shared SA is in this list because the --move step proved (live, 2026-07-29)
# that its grant on the 9 core sheets was INHERITED from the RidingHigh-Data root,
# not direct: after moving them into the canonical folder they dropped from 5
# permissions to 4, losing exactly ridinghigh-sheets-v2. That SA is the fallback
# credential for ~20 modules, so it must be re-granted explicitly. Target parity
# is the 2026-07 sheets, which carry all five.
REQUIRED_SAS = [
    ("ridinghigh-auto-scan@ridinghigh-pro-v2.iam.gserviceaccount.com", "writer"),
    ("id-ridinghigh-agent-minute@ridinghigh-pro-v2.iam.gserviceaccount.com", "writer"),
    ("ridinghigh-health-audit@ridinghigh-pro-v2.iam.gserviceaccount.com", "reader"),
    (SHARED_SA, "writer"),
]


def _drive():
    drive = sheets_manager._get_drive_service_oauth()
    if drive is None:
        print("FATAL: no OAuth credentials — cannot proceed")
        sys.exit(1)
    return drive


def _august_tabs():
    """{logical_name: file_id} for the active month, from sheets_config.json."""
    config = json.load(open(sheets_manager.CONFIG_PATH))
    month = config.get("months", config)
    return month.get(MONTH, {})


def _resolve_month_folder(drive, month, create=False, allow_missing=False):
    """Return the canonical month folder id for `month`, under CANON_ROOT.

    Never uses sheets_manager._get_root_folder_id — that helper resolves the root
    through the shared service account, which has no permission on the canonical
    root, and is exactly the bug this script exists to work around.

    Fail-closed on duplicates: more than one folder with that name under the
    canonical root means the cross-root split is happening again, and picking one
    silently is how 2026-08 ended up half-provisioned.
    """
    if month == DEFAULT_MONTH:
        return CANON_AUG

    q = (f"name='{month}' and '{CANON_ROOT}' in parents "
         f"and mimeType='application/vnd.google-apps.folder' and trashed=false")
    found = drive.files().list(q=q, fields="files(id,name)").execute().get("files", [])

    if len(found) > 1:
        raise RuntimeError(
            f"DUPLICATE FOLDER GUARD: {len(found)} folders named '{month}' under the "
            f"canonical root: {[f['id'] for f in found]} — refusing to guess.")
    if found:
        print(f"  FOLDER / {found[0]['id']} / FOUND existing {month} under canonical root")
        return found[0]["id"]

    if not create:
        if allow_missing:
            print(f"  FOLDER / (none) / DRY-RUN would create {month} under the "
                  f"canonical root")
            return None
        raise RuntimeError(
            f"No folder named '{month}' under the canonical root (pass a command "
            f"that creates it).")

    meta = {"name": month, "mimeType": "application/vnd.google-apps.folder",
            "parents": [CANON_ROOT]}
    folder_id = drive.files().create(body=meta, fields="id").execute()["id"]
    sheets_manager._share_with_service_account(drive, folder_id)
    print(f"  FOLDER / {folder_id} / CREATED {month} under canonical root + shared SA")
    return folder_id


def _perms(drive, file_id):
    res = drive.permissions().list(
        fileId=file_id,
        fields="permissions(id,type,role,emailAddress)",
        pageSize=100,
    ).execute()
    return res.get("permissions", [])


def _describe(drive, name, file_id):
    """Return (parents, {email: role}) for one sheet."""
    meta = drive.files().get(fileId=file_id, fields="id,name,parents,trashed").execute()
    perms = {p.get("emailAddress"): p.get("role") for p in _perms(drive, file_id)}
    return meta, perms


def cmd_audit(drive):
    tabs = _august_tabs()
    print(f"AUDIT {MONTH} — {len(tabs)} tab(s) in sheets_config.json")
    print(f"  CANON_TARGET={TARGET_FOLDER}  BAD_AUG={BAD_AUG}")

    in_canon = in_bad = elsewhere = 0
    fully_shared = 0
    missing_map = {}

    for name in sorted(tabs):
        file_id = tabs[name]
        try:
            meta, perms = _describe(drive, name, file_id)
        except Exception as exc:
            print(f"  AUDIT / {file_id} / GET_FAIL {name}: {exc}")
            continue

        parents = meta.get("parents", [])
        if TARGET_FOLDER in parents:
            where, marker = "CANON", "✓"
            in_canon += 1
        elif BAD_AUG in parents:
            where, marker = "BAD  ", "✗"
            in_bad += 1
        else:
            where, marker = "OTHER", "?"
            elsewhere += 1

        missing = [email for email, _role in REQUIRED_SAS if email not in perms]
        missing_map[name] = missing
        if not missing:
            fully_shared += 1

        short = [
            ("AS" if "auto-scan" in e else "AM" if "agent-minute" in e else
             "HA" if "health-audit" in e else "SHARED" if e == SHARED_SA else
             "OWNER" if r == "owner" else e)
            for e, r in perms.items()
        ]
        print(f"  {marker} {name:<18} {file_id}  parent={where}  "
              f"perms={len(perms)} [{','.join(sorted(short))}]"
              + (f"  MISSING={[m.split('@')[0] for m in missing]}" if missing else ""))

    print(f"SUMMARY: total={len(tabs)} in_canon={in_canon} in_bad={in_bad} "
          f"elsewhere={elsewhere} fully_shared={fully_shared}")

    # Inheritance verdict: judged only on sheets that already live in CANON_AUG.
    canon_names = [
        n for n in sorted(tabs)
        if TARGET_FOLDER in drive.files().get(
            fileId=tabs[n], fields="parents").execute().get("parents", [])
    ]
    if not canon_names:
        print("INHERITANCE=UNKNOWN (no sheet currently under the canonical folder)")
    elif all(not missing_map.get(n) for n in canon_names):
        print(f"INHERITANCE=WORKS (all {len(canon_names)} sheet(s) under the canonical "
              f"folder carry _AS/_AM/_HA)")
    else:
        broken = [n for n in canon_names if missing_map.get(n)]
        print(f"INHERITANCE=BROKEN ({len(broken)}/{len(canon_names)} sheet(s) under the "
              f"canonical folder missing a required SA: {broken[:5]})")
    return missing_map


def cmd_move(drive, apply_changes):
    """Move every 2026-08 sheet that is not already under CANON_AUG."""
    tabs = _august_tabs()
    moved = skipped = failed = 0

    for name in sorted(tabs):
        file_id = tabs[name]
        meta = drive.files().get(fileId=file_id, fields="id,parents").execute()
        parents = meta.get("parents", [])

        if TARGET_FOLDER in parents:
            print(f"  MOVE / {file_id} / SKIP already in CANON_AUG ({name})")
            skipped += 1
            continue

        remove = ",".join(parents)
        if not apply_changes:
            print(f"  MOVE / {file_id} / DRY-RUN would move {name}: "
                  f"{parents} -> {TARGET_FOLDER}")
            moved += 1
            continue

        try:
            drive.files().update(
                fileId=file_id,
                addParents=TARGET_FOLDER,
                removeParents=remove,
                fields="id,parents",
            ).execute()
            print(f"  MOVE / {file_id} / OK {name} -> CANON_AUG")
            moved += 1
        except Exception as exc:
            print(f"  MOVE / {file_id} / FAIL {name}: {exc}")
            failed += 1

    print(f"MOVE SUMMARY: moved={moved} skipped={skipped} failed={failed} "
          f"apply={apply_changes}")


def cmd_reshare(drive, apply_changes):
    """Grant _AS/_AM/_HA on every 2026-08 sheet that lacks them. Idempotent."""
    tabs = _august_tabs()
    granted = skipped = failed = 0

    for name in sorted(tabs):
        file_id = tabs[name]
        try:
            existing = {p.get("emailAddress") for p in _perms(drive, file_id)}
        except Exception as exc:
            print(f"  RESHARE / {file_id} / FAIL list {name}: {exc}")
            failed += 1
            continue

        for email, role in REQUIRED_SAS:
            if email in existing:
                print(f"  RESHARE / {file_id} / SKIP {name} {email.split('@')[0]} "
                      f"already present")
                skipped += 1
                continue

            if not apply_changes:
                print(f"  RESHARE / {file_id} / DRY-RUN would grant {name} "
                      f"{email.split('@')[0]} as {role}")
                granted += 1
                continue

            try:
                drive.permissions().create(
                    fileId=file_id,
                    body={"type": "user", "role": role, "emailAddress": email},
                    sendNotificationEmail=False,
                ).execute()
                print(f"  RESHARE / {file_id} / OK {name} {email.split('@')[0]} "
                      f"as {role}")
                granted += 1
            except Exception as exc:
                print(f"  RESHARE / {file_id} / FAIL {name} "
                      f"{email.split('@')[0]}: {exc}")
                failed += 1

    print(f"RESHARE SUMMARY: granted={granted} skipped={skipped} failed={failed} "
          f"apply={apply_changes}")


def cmd_provision_core(drive, apply_changes):
    """Create the SHEET_NAMES core sheets for MONTH in the canonical month folder.

    Mirrors what prepare_next_month does — create + share, no headers — but goes
    through OAuth and the canonical root, so it cannot land in RidingHigh-Data.
    Idempotent: an existing file with the same name in the folder is reused.
    """
    created = skipped = failed = 0
    ids = {}

    if TARGET_FOLDER is None:
        for name in sheets_manager.SHEET_NAMES:
            print(f"  PROVISION / (none) / DRY-RUN would create RH-{MONTH}-{name}")
        print(f"PROVISION SUMMARY: created={len(sheets_manager.SHEET_NAMES)} skipped=0 "
              f"failed=0 apply={apply_changes} (month folder does not exist yet)")
        return

    for name in sheets_manager.SHEET_NAMES:
        display_name = f"RH-{MONTH}-{name}"
        q = (f"name='{display_name}' and '{TARGET_FOLDER}' in parents "
             f"and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false")
        found = drive.files().list(q=q, fields="files(id)").execute().get("files", [])

        if found:
            ids[name] = found[0]["id"]
            print(f"  PROVISION / {found[0]['id']} / SKIP {name} already in folder")
            skipped += 1
            continue

        if not apply_changes:
            print(f"  PROVISION / (none) / DRY-RUN would create {display_name}")
            created += 1
            continue

        try:
            meta = {"name": display_name,
                    "mimeType": "application/vnd.google-apps.spreadsheet",
                    "parents": [TARGET_FOLDER]}
            sheet_id = drive.files().create(body=meta, fields="id").execute()["id"]
            sheets_manager._share_with_service_account(drive, sheet_id)
            ids[name] = sheet_id
            print(f"  PROVISION / {sheet_id} / OK created {display_name} + shared SA")
            created += 1
        except Exception as exc:
            print(f"  PROVISION / (none) / FAIL {name}: {exc}")
            failed += 1

    if apply_changes and ids:
        # MERGE into the existing month entry — replacing it wholesale would wipe
        # agent tabs that create_agent_sheets registered earlier.
        config = sheets_manager._load_config()
        month_cfg = dict(config.get(MONTH, {}))
        added = [k for k in ids if k not in month_cfg]
        month_cfg.update(ids)
        config[MONTH] = month_cfg
        sheets_manager._save_config(config)
        print(f"  CONFIG / sheets_config.json / OK merged {len(added)} new key(s) "
              f"into {MONTH}, month now has {len(month_cfg)} tab(s)")

    print(f"PROVISION SUMMARY: created={created} skipped={skipped} failed={failed} "
          f"apply={apply_changes}")


def main():
    global MONTH, TARGET_FOLDER

    parser = argparse.ArgumentParser(description="TASK-242 month provisioning repair")
    parser.add_argument("--month", default=DEFAULT_MONTH,
                        help=f"month key to operate on (default {DEFAULT_MONTH})")
    parser.add_argument("--audit", action="store_true", help="read-only report")
    parser.add_argument("--move", action="store_true",
                        help="move the month's sheets into the canonical month folder")
    parser.add_argument("--reshare", action="store_true",
                        help="grant _AS/_AM/_HA/shared-SA on the month's sheets")
    parser.add_argument("--provision-core", action="store_true",
                        help="create the SHEET_NAMES core sheets in the canonical folder")
    parser.add_argument("--apply", action="store_true",
                        help="actually write (default is dry-run)")
    args = parser.parse_args()

    if not (args.audit or args.move or args.reshare or args.provision_core):
        parser.error("pick one of --audit / --move / --reshare / --provision-core")

    drive = _drive()

    MONTH = args.month
    # Only --provision-core may create the month folder; the others must find it.
    TARGET_FOLDER = _resolve_month_folder(
        drive, MONTH,
        create=args.provision_core and args.apply,
        allow_missing=args.provision_core and not args.apply)
    print(f"MONTH={MONTH}  TARGET_FOLDER={TARGET_FOLDER}")

    if args.provision_core:
        cmd_provision_core(drive, args.apply)
    if args.audit:
        cmd_audit(drive)
    if args.move:
        cmd_move(drive, args.apply)
    if args.reshare:
        cmd_reshare(drive, args.apply)


if __name__ == "__main__":
    main()
