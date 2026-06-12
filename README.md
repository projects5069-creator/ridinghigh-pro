# 🚀 RidingHigh Pro

Automated short-selling research and analysis system for US equities.

**Status:** Phase 1 — data accumulation & validation. No real-money trading.

## 📚 Documentation

The complete system reference is in **[`docs/RidingHigh_Pro_PK_v2.md`](docs/RidingHigh_Pro_PK_v2.md)** — a 36-section production-grade master document covering architecture, data pipelines, scoring, health monitoring, runbooks, ADRs, and the disaster recovery plan.

For specific topics:
- **Open issues:** [`OPEN_ISSUES.md`](OPEN_ISSUES.md)
- **Health audit system:** [`README_health_audit.md`](README_health_audit.md)
- **Code conventions:** [`CLAUDE.md`](CLAUDE.md)
- **Auto-generated state:** `PROJECT_STATE.md` — local-only, **not in the repo** (gitignored). Regenerate it after a fresh clone / cloud run with `uv run python3 generate_project_state.py` (TASK-161).

## 🔧 Quick Links

- **Dashboard (live):** [ridinghigh-pro-v2.streamlit.app](https://ridinghigh-pro-v2.streamlit.app)
- **Master backup (Google Sheet):** [System Reference Sheet](https://docs.google.com/spreadsheets/d/1SuHj0joCfT7kAoSEvrqepJJcUG8uBU5J4zmxkx9e3J0)
- **Companion system:** [Ambroseius/DropsLab](https://github.com/Ambroseius/DropsLab)

## 🌍 Owner

Amihay Levy · Lima, Peru (UTC-5)

## 📦 Repository conventions

Files prefixed `DEPRECATED_YYYY-MM-DD_*` are historical reference only. They reflect prior versions of the system and should not be used as authoritative documentation. Always defer to the file paths listed under "Documentation" above.

---

*This README is intentionally short. For depth, see the [PK document](docs/RidingHigh_Pro_PK_v2.md).*
