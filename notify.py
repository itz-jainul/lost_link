import smtplib
from email.message import EmailMessage
from datetime import datetime
from config import Config

try:
    from twilio.rest import Client as TwilioClient
    _TWILIO_AVAILABLE = True
except Exception:
    _TWILIO_AVAILABLE = False

def send_email(to_email: str, subject: str, body: str):
    if Config.MAIL_SERVER and Config.MAIL_PORT and Config.MAIL_USERNAME and Config.MAIL_PASSWORD:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = Config.MAIL_USERNAME
        msg['To'] = to_email
        msg.set_content(body)
        try:
            if Config.MAIL_USE_SSL:
                server = smtplib.SMTP_SSL(Config.MAIL_SERVER, Config.MAIL_PORT)
            else:
                server = smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT)
            server.ehlo()
            if Config.MAIL_USE_TLS:
                server.starttls()
            server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print("Failed to send email:", e)
            return False
    else:
        print("=== EMAIL (demo) ===")
        print("To:", to_email)
        print("Subject:", subject)
        print(body)
        print("====================")
        return True

def send_sms(to_number: str, body: str):
    if _TWILIO_AVAILABLE and Config.TWILIO_SID and Config.TWILIO_TOKEN and Config.TWILIO_FROM:
        try:
            client = TwilioClient(Config.TWILIO_SID, Config.TWILIO_TOKEN)
            msg = client.messages.create(body=body, from_=Config.TWILIO_FROM, to=to_number)
            print("SMS sent:", msg.sid)
            return True
        except Exception as e:
            print("Failed to send SMS:", e)
            return False
    else:
        print("=== SMS (demo) ===")
        print("To:", to_number)
        print(body)
        print("==================")
        return True
