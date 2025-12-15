import os
import sys
from pathlib import Path
from unittest import mock, TestCase

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services import email_service


class EmailServiceTests(TestCase):
    def test_send_otp_email_uses_smtp_ssl_and_sends_message(self):
        env = {
            "SMTP_HOST": "smtp.test.com",
            "SMTP_PORT": "2525",
            "SMTP_USER": "user@test.com",
            "SMTP_PASS": "secret-pass",
            "SMTP_FROM": "from@test.com",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch("app.services.email_service.ssl.create_default_context", return_value=mock.Mock()) as mock_ctx:
                with mock.patch("app.services.email_service.smtplib.SMTP_SSL") as mock_smtp:
                    email_service.send_otp_email("rcpt@test.com", "654321")

        mock_smtp.assert_called_once_with(
            "smtp.test.com",
            2525,
            context=mock.ANY,
            timeout=30,
        )
        mock_ctx.assert_called_once()
        server = mock_smtp.return_value.__enter__.return_value
        server.login.assert_called_once_with("user@test.com", "secret-pass")
        server.send_message.assert_called_once()
        sent_msg = server.send_message.call_args[0][0]
        self.assertEqual(sent_msg["To"], "rcpt@test.com")
        self.assertEqual(sent_msg["From"], "from@test.com")
        self.assertEqual(sent_msg["Subject"], "Your FurEver Home OTP Code")
        self.assertIn("654321", sent_msg.get_content())

    def test_missing_config_raises(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.dict(
                email_service.SMTP_DEFAULTS,
                {"host": "", "port": 0, "user": "", "password": "", "sender": ""},
                clear=True,
            ):
                with self.assertRaises(RuntimeError):
                    email_service.send_otp_email("rcpt@test.com", "123456")


if __name__ == "__main__":
    import unittest

    unittest.main()
