import asyncio
import smtplib
from email.message import EmailMessage

from app.core.config import Settings


class EmailService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def send_password_reset_email(
        self,
        to_email: str,
        reset_url: str,
    ) -> bool:
        if not self.settings.smtp_enabled:
            return False

        if not self.settings.smtp_host:
            return False

        return await asyncio.to_thread(
            self._send_password_reset_email_sync,
            to_email,
            reset_url,
        )

    def _send_password_reset_email_sync(
        self,
        to_email: str,
        reset_url: str,
    ) -> bool:
        message = EmailMessage()
        message["Subject"] = "Сброс пароля KOYASH"
        message["From"] = f"{self.settings.smtp_from_name} <{self.settings.smtp_from_email}>"
        message["To"] = to_email

        message.set_content(
            "\n".join(
                [
                    "Здравствуйте!",
                    "",
                    "Вы запросили сброс пароля для аккаунта KOYASH.",
                    "Чтобы задать новый пароль, откройте ссылку:",
                    "",
                    reset_url,
                    "",
                    (
                        "Ссылка действует ограниченное время и может быть использована "
                        "только один раз."
                    ),
                    "",
                    "Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.",
                    "",
                    "KOYASH",
                ]
            )
        )

        try:
            if self.settings.smtp_port == 465:
                with smtplib.SMTP_SSL(
                    self.settings.smtp_host,
                    self.settings.smtp_port,
                    timeout=15,
                ) as smtp:
                    self._login_if_needed(smtp)
                    smtp.send_message(message)
            else:
                with smtplib.SMTP(
                    self.settings.smtp_host,
                    self.settings.smtp_port,
                    timeout=15,
                ) as smtp:
                    smtp.starttls()
                    self._login_if_needed(smtp)
                    smtp.send_message(message)
        except Exception:
            return False

        return True

    def _login_if_needed(self, smtp: smtplib.SMTP) -> None:
        if self.settings.smtp_username and self.settings.smtp_password:
            smtp.login(
                self.settings.smtp_username,
                self.settings.smtp_password,
            )
