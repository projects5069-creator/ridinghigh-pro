"""Unit tests for EmailSender — all SMTP calls mocked."""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from agent.notifications.email_sender import EmailSender, send_alert


class TestConfiguration:
    def test_reads_env_vars(self):
        with patch.dict(os.environ, {
            "SMTP_HOST": "smtp.test.com",
            "SMTP_PORT": "465",
            "SMTP_USER": "user@test.com",
            "SMTP_PASSWORD": "abcd efgh ijkl mnop",
            "EMAIL_TO": "to@test.com",
        }):
            sender = EmailSender()
            assert sender.host == "smtp.test.com"
            assert sender.port == 465
            assert sender.user == "user@test.com"
            assert sender.password == "abcdefghijklmnop"  # spaces stripped
            assert sender.recipient == "to@test.com"

    def test_is_configured_true_when_all_set(self):
        sender = EmailSender(user="u", password="p", recipient="r")
        assert sender.is_configured() is True

    def test_is_configured_false_when_missing(self):
        sender = EmailSender(user="", password="", recipient="")
        assert sender.is_configured() is False


class TestSend:
    @patch("agent.notifications.email_sender.smtplib.SMTP")
    def test_send_success(self, mock_smtp_class):
        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp

        sender = EmailSender(host="smtp.test.com", port=587, user="u@t.com", password="pwd", recipient="r@t.com")
        result = sender.send("Test", "<p>Hello</p>")

        assert result is True
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("u@t.com", "pwd")
        mock_smtp.send_message.assert_called_once()

    @patch("agent.notifications.email_sender.smtplib.SMTP")
    def test_send_failure_returns_false(self, mock_smtp_class):
        mock_smtp_class.side_effect = Exception("Connection refused")

        sender = EmailSender(host="bad", port=587, user="u", password="p", recipient="r")
        result = sender.send("Test", "<p>Hi</p>")

        assert result is False  # graceful failure, no exception raised

    def test_send_skipped_when_not_configured(self):
        sender = EmailSender(user="", password="", recipient="")
        result = sender.send("Test", "<p>Hi</p>")
        assert result is False


class TestHtmlToPlain:
    def test_strips_tags(self):
        html = "<p>Hello <strong>World</strong></p>"
        plain = EmailSender._html_to_plain(html)
        assert "Hello" in plain
        assert "World" in plain
        assert "<" not in plain

    def test_br_becomes_newline(self):
        html = "Line1<br>Line2<br/>Line3"
        plain = EmailSender._html_to_plain(html)
        assert "Line1\nLine2\nLine3" in plain


class TestSendAlert:
    @patch("agent.notifications.email_sender.send_email")
    def test_alert_uses_warning_subject(self, mock_send):
        mock_send.return_value = True
        send_alert("Test error", "Stack trace here")

        call_args = mock_send.call_args
        subject = call_args[0][0]
        body = call_args[0][1]

        assert "🚨" in subject
        assert "Test error" in subject
        assert "Stack trace here" in body
