"""T-201 (Sprint 1) — send_alert must throttle identical alerts.

Leg B of T-201: without a throttle, a 429-storm means errors>0 every minute
⇒ an email every minute (the 25-duplicate-email precedent). The throttle is
an idempotency-key (the error_summary) checked against system_events rows
within a 30-minute window, using the read that already exists in the cycle
(sheets_manager.get_sheet_records("system_events"), orchestrator.py:146).
RED before fix.
"""
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from agent.notifications.email_sender import send_alert

PERU = timezone(timedelta(hours=-5))


def _harness():
    """In-memory stand-ins for the system_events reader/writer + SMTP sender."""
    sent, events = [], []

    def fake_sender(subject, html):
        sent.append(subject)
        return True

    def reader():
        return list(events)

    def writer(row):
        events.append({
            "Timestamp": row[0], "EventType": row[1], "Severity": row[2],
            "Component": row[3], "Message": row[4], "Details": row[5],
            "ActionTaken": row[6],
        })

    return sent, events, fake_sender, reader, writer


def test_two_identical_alerts_within_window_send_once():
    sent, events, fake_sender, reader, writer = _harness()
    t0 = datetime(2026, 8, 7, 10, 0, 0, tzinfo=PERU)

    ok1 = send_alert("5 error(s) in agent run", "details", sender=fake_sender,
                     event_reader=reader, event_writer=writer, now=t0)
    ok2 = send_alert("5 error(s) in agent run", "details", sender=fake_sender,
                     event_reader=reader, event_writer=writer,
                     now=t0 + timedelta(minutes=5))

    assert ok1 is True, "first alert must go out"
    assert ok2 is False, "identical alert 5 min later must be throttled"
    assert len(sent) == 1, f"expected exactly one email, got {len(sent)}"


def test_alert_sends_again_after_window_expires():
    sent, events, fake_sender, reader, writer = _harness()
    t0 = datetime(2026, 8, 7, 10, 0, 0, tzinfo=PERU)

    send_alert("Sentinel HALT: quota", "d", sender=fake_sender,
               event_reader=reader, event_writer=writer, now=t0)
    ok2 = send_alert("Sentinel HALT: quota", "d", sender=fake_sender,
                     event_reader=reader, event_writer=writer,
                     now=t0 + timedelta(minutes=31))

    assert ok2 is True and len(sent) == 2, (
        f"31 min > 30-min window ⇒ must send again (sent={len(sent)})"
    )


def test_uninjected_call_without_smtp_never_touches_sheets(monkeypatch):
    """Regression: on 2026-08-07 the default reader/writer did live Sheets
    I/O from an uninjected test call and wrote a real ALERT_EMAIL row to
    production system_events. Without SMTP configured there is no storm to
    throttle — the default I/O must not run at all."""
    import agent.notifications.email_sender as es

    for var in ("SMTP_USER", "SMTP_PASSWORD", "EMAIL_TO"):
        monkeypatch.delenv(var, raising=False)

    def _explode(*a, **k):
        raise AssertionError("default Sheets I/O must not be touched")

    monkeypatch.setattr(es, "_default_event_reader", _explode)
    monkeypatch.setattr(es, "_default_event_writer", _explode)

    sent = []

    def fake_sender(subject, html):
        sent.append(subject)
        return True

    ok = es.send_alert("Test error", "Stack trace here", sender=fake_sender)
    assert ok is True and len(sent) == 1, (
        f"uninjected+unconfigured call must send normally (ok={ok}, sent={len(sent)})"
    )
    assert "🚨" in sent[0] and "Test error" in sent[0]


def test_different_summary_within_window_is_not_throttled():
    sent, events, fake_sender, reader, writer = _harness()
    t0 = datetime(2026, 8, 7, 10, 0, 0, tzinfo=PERU)

    send_alert("5 error(s) in agent run", "d", sender=fake_sender,
               event_reader=reader, event_writer=writer, now=t0)
    ok2 = send_alert("Sentinel HALT: quota", "d", sender=fake_sender,
                     event_reader=reader, event_writer=writer,
                     now=t0 + timedelta(minutes=1))

    assert ok2 is True and len(sent) == 2, (
        "a different idempotency-key must not be throttled"
    )
