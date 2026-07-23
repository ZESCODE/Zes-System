"""Async email (SMTP send + IMAP read)."""
import asyncio, imaplib, email, base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List, Dict, Any, Optional
import aiosmtplib


class EmailSkill:
    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str,
                 use_tls: bool = True, imap_host: Optional[str] = None, imap_port: int = 993):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.imap_host = imap_host or smtp_host
        self.imap_port = imap_port

    async def send_email(self, to: List[str], subject: str, body: str,
                         html: Optional[str] = None, from_addr: Optional[str] = None,
                         attachments: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_addr or self.username
            msg["To"] = ", ".join(to)
            msg.attach(MIMEText(body, "plain"))
            if html:
                msg.attach(MIMEText(html, "html"))
            if attachments:
                for att in attachments:
                    part = MIMEApplication(att["content"], Name=att["filename"])
                    part["Content-Disposition"] = f'attachment; filename="{att["filename"]}"'
                    msg.attach(part)
            smtp = aiosmtplib.SMTP(hostname=self.smtp_host, port=self.smtp_port, use_tls=self.use_tls)
            await smtp.login(self.username, self.password)
            await smtp.sendmail(msg["From"], to, msg.as_string())
            await smtp.quit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def read_inbox(self, limit: int = 10, unseen_only: bool = True,
                         subject_filter: Optional[str] = None) -> Dict[str, Any]:
        try:
            def _sync_read():
                mail = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
                mail.login(self.username, self.password)
                mail.select("INBOX")
                status, data = mail.search(None, "UNSEEN" if unseen_only else "ALL")
                if status != "OK":
                    raise Exception("Search failed")
                email_ids = data[0].split()[-limit:] if limit else data[0].split()
                messages = []
                for eid in email_ids:
                    status, msg_data = mail.fetch(eid, "(RFC822)")
                    if status != "OK":
                        continue
                    raw = msg_data[0][1]
                    msg = email.message_from_bytes(raw)
                    subj = msg["Subject"]
                    if subject_filter and subject_filter.lower() not in (subj or "").lower():
                        continue
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                                break
                    else:
                        body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
                    messages.append({"id": eid.decode(), "from": msg["From"],
                                     "subject": subj, "body": body, "date": msg["Date"]})
                mail.close()
                mail.logout()
                return messages
            loop = asyncio.get_running_loop()
            messages = await loop.run_in_executor(None, _sync_read)
            return {"success": True, "messages": messages}
        except Exception as e:
            return {"success": False, "error": str(e)}
