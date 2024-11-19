from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import smtplib

class MailSender:
    def __init__(self, sender, password, smtp_server, port):
        self.sender = sender
        self.password = password
        self.smtp_server = smtp_server
        self.port = port
    def send_mail_without_attachment(self, receiver, subject, body):
            """Send an email without any attachment."""
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = receiver
            msg['Subject'] = subject

            body_part = MIMEText(body, 'plain')
            msg.attach(body_part)

            self.send_mail(msg)

    def send_mail(self, msg):
        """Send the email via SMTP server."""
        server = smtplib.SMTP_SSL(self.smtp_server, self.port)
        server.login(self.sender, self.password)
        server.sendmail(self.sender, msg['To'], msg.as_string())
        server.quit()



