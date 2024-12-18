import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from config import get_config

def send_email_response(to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = get_config("SMTP", "SMTP_USER")
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP(get_config("SMTP", "SMTP_SERVER"), get_config("SMTP", "SMTP_PORT"))
        server.starttls()
        server.login(get_config("SMTP", "SMTP_USER"), get_config("SMTP", "SMTP_PASSWORD"))
        server.sendmail(get_config("SMTP", "SMTP_USER"), to_email, msg.as_string())
        server.quit()
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")

def clear_console():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')
