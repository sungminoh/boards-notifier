# -*- coding: utf-8 -*-
import smtplib
from email.mime.text import MIMEText


class EmailHandler(object):
    @staticmethod
    def send_email(subject, sender, receiver, content, password=''):
        msg = MIMEText(content.encode('utf-8'), _charset='utf-8')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = ', '.join(receiver)
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.ehlo()
            server.starttls()
            server.login(sender.split('@')[0], password)
            server.sendmail(sender, receiver, msg.as_string())
            server.close()
            print('successfully sent the mail to %s' % msg['To'])
        except Exception:
            print('send through localhost')
            s = smtplib.SMTP('localhost')
            s.sendmail(sender, receiver, msg.as_string())
            s.quit()
            print('successfully sent the mail to %s' % msg['To'])
