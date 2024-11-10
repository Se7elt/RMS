import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import imaplib
import email
from email.header import decode_header
from config_utils import initialize_config
import configparser


config = initialize_config()

SMTP_SERVER = config["EMAIL"]["SMTP_SERVER"]
SMTP_PORT = config["EMAIL"]["SMTP_PORT"]
SMTP_USER = config["EMAIL"]["SMTP_USER"]
SMTP_PASSWORD = config["EMAIL"]["SMTP_PASSWORD"]
IMAP_SERVER = config["EMAIL"]["IMAP_SERVER"]
IMAP_USER = config["EMAIL"]["IMAP_USER"]
IMAP_PASSWORD = config["EMAIL"]["IMAP_PASSWORD"]



def send_email_response(to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
        print(f"Email отправлен на {to_email}")
    except Exception as e:
        print(f"Ошибка при отправке email: {e}")


def get_email_response(subject_filter):
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(IMAP_USER, IMAP_PASSWORD)
        mail.select("inbox")
        status, messages = mail.search(None, f'(SUBJECT "{subject_filter}")')
        email_ids = messages[0].split()

        for email_id in email_ids:
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])

                    # Проверка заголовка и декодирование
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")

                    # Проверка и декодирование тела письма
                    body = None
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                payload = part.get_payload(decode=True)
                                if payload:
                                    body = payload.decode("utf-8", errors="replace")
                    else:
                        payload = msg.get_payload(decode=True)
                        if payload:
                            body = payload.decode("utf-8", errors="replace")

                    mail.store(email_id, '+FLAGS', '\\Deleted')
                    mail.expunge()
                    return body if body else None

        mail.logout()
    except Exception as e:
        print(f"Ошибка при получении email ответа: {e}")
    return None