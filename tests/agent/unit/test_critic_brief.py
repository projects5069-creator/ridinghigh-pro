"""TASK-48 EMAIL.1 — RED tests: critic_brief AutoLessons rendering + anti-silent-drop.
Written before implementation. _lessons_to_bullets missing → AttributeError expected.
NOTE: this file is created via a single-quoted heredoc so backslash-escapes are literal."""
import importlib
import pytest

cb = importlib.import_module("agent.notifications.templates.critic_brief")


def _bul(raw):
    return cb._lessons_to_bullets(raw)


# 1. newline אמיתי → 3 פריטים
def test_real_newline_three_items():
    assert _bul("a\nb\nc").count("<li>") == 3

# 2. \n ספרותי (שני תווים: backslash + n) → 2 פריטים
def test_literal_backslash_n_two_items():
    raw = "a\\nb"           # heredoc מצוטט → באמת backslash+n
    assert len(raw) == 4    # מאמת שזה ספרותי ולא newline אמיתי
    assert _bul(raw).count("<li>") == 2

# 3. \r\n → 2
def test_crlf_two_items():
    assert _bul("a\r\nb").count("<li>") == 2

# 4. ריק → בלי <ul>
def test_empty_graceful():
    assert "<ul>" not in _bul("")

# 5. שורה בודדת → לכל היותר פריט אחד
def test_single_line():
    assert _bul("only one line").count("<li>") <= 1

# 6. escape: <script> → &lt;script&gt;
def test_html_escape():
    html = _bul("<script>x")
    assert "<script>" not in html and "&lt;script&gt;" in html

# 7. escape לא שובר emoji
def test_escape_keeps_emoji():
    html = _bul("🟢 ניצחון\n<b>x")
    assert "🟢" in html and "<b>" not in html and "&lt;b&gt;" in html

# 8. כרטיס win/loss — צבע + ticker
def test_render_card_win_loss_colors():
    subject, html = cb.render_critic_email(
        facts={},
        positions={},
        postmortems=[
            {"Ticker": "AAAA", "PnLPct": 10.5, "ExitReason": "TP_HIT", "AutoLessons": "win\nlesson"},
            {"Ticker": "BBBB", "PnLPct": -9.8, "ExitReason": "SL_HIT", "AutoLessons": "loss\nlesson"},
        ],
    )
    assert "AAAA" in html and "BBBB" in html
    assert "#10b981" in html and "#ef4444" in html

# 9. None vs [] — חיני
@pytest.mark.parametrize("pm", [None, []])
def test_postmortems_none_or_empty(pm):
    subject, html = cb.render_critic_email(facts={}, positions={}, postmortems=pm)
    assert isinstance(html, str)

# 10. anti-silent-drop: יום ללא כניסות אך עסקה סגורה → forensic חייב להופיע
def test_forensic_not_dropped_when_no_activity():
    subject, html = cb.render_critic_email(
        facts={"has_activity": False, "anomalies": [], "conflicts": []},
        positions={},
        postmortems=[{"Ticker": "CCCC", "PnLPct": 7.2, "ExitReason": "TP_HIT", "AutoLessons": "x\ny"}],
    )
    assert "CCCC" in html


# 11. כותרת הכרטיס מציגה PnL% + ExitReason (AC #2)
def test_card_header_shows_pnl_and_exit():
    subject, html = cb.render_critic_email(
        facts={}, positions={},
        postmortems=[{"Ticker": "DDDD", "PnLPct": 12.5, "ExitReason": "TP_HIT", "AutoLessons": "x\ny"}],
    )
    assert "12.5" in html and "TP_HIT" in html
