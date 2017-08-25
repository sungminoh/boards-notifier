# -*- coding: utf-8 -*-

import requests
from time import sleep
from lxml import html
from itertools import chain
import cPickle as pk
import smtplib
from email.mime.text import MIMEText
import argparse
import platform
import re
import os


GMAIL_ACCOUNT = '<account without @gmail.com>'
GMAIL_PASSWORD = '<password>'
SNULIFE_ACCOUNT = '<snulife account>'
SNULIFE_PASSWORD = '<snulife password>'
TITLE = u'스누라이프 알리미 입니다.'


SNULIFE_CONSTANT = {
    'post_class': 'hx',
    'target': 'http://snulife.com/housing/'
}


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
            print 'successfully sent the mail to %s' % msg['To']
        except Exception:
            s = smtplib.SMTP('localhost')
            s.sendmail(sender, receiver, msg.as_string())
            s.quit()
            print "send through localhost"
            print 'successfully sent the mail to %s' % msg['To']


class Snulife(object):
    saved = './tmp.pkl'

    data = {'act': 'procMemberLogin',
            'mid': 'main',
            'success_return_url': 'http://snulife.com/main',
            'keep_signed': 'Y'}

    header = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
              'Accept-Encoding': 'gzip, deflate, br',
              'Accept-Language': 'en-US,en;q=0.8,ko;q=0.6',
              'Cache-Control': 'no-cache',
              'Connection': 'keep-alive',
              'Content-Length': '112',
              'Content-Type': 'application/x-www-form-urlencoded',
              'Host': 'snulife.com',
              'Origin': 'http://snulife.com',
              'POST / HTTP/1.1': '',
              'Pragma': 'no-cache',
              'Referer': 'http://snulife.com/main',
              'Upgrade-Insecure-Requests': '1'}

    base = 'http://snulife.com'
    login = 'https://snulife.com/'

    def __init__(self, user_id, password):
        self.s = requests.session()
        self.data['user_id'] = user_id
        self.data['password'] = password

    def connect(self):
        self.s.post(self.login, self.data, headers=self.header)
        return self

    def get(self, url):
        text = self.s.get(url).text
        self.tree = html.fromstring(text)
        return self

    def is_same(self):
        if os.path.isfile(Snulife.saved):
            with open(Snulife.saved) as f:
                return pk.load(f) == self.titles
        return False

    def make_content(self):
        return '\n'.join(chain(*zip(self.titles, self.links)))

    def find_all(self, class_name, regex=''):
        self.titles = []
        self.links = []
        for e in self.tree.find_class(class_name):
            link = Snulife.base + e.values()[0]
            title = e.text_content().strip()
            if not re.search(regex, title):
                continue
            self.links.append(link)
            self.titles.append(title)
        return self

    def send_email(self, title, sender, receiver, password=''):
        content = self.make_content()
        sender = sender if '@' in sender else '%s@gmail.com' % sender
        EmailHandler.send_email(title, sender, receiver, content, password)

    def noti(self, title, sender, receiver, password=''):
        content = self.make_content()
        print content
        if self.is_same():
            print 'no new post'
        else:
            print 'got new post'
            with open(Snulife.saved, 'wb') as f:
                pk.dump(self.titles, f)
                self.send_email(title, sender, receiver, password)

    def crawl(self, url='', class_name='', regex=''):
        self.connect().get(url).find_all(class_name, regex)
        print self.make_content()
        return self


def get_args():
    description = 'snulife new post alarm'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--user_id', '-u',
                        # required=True,
                        type=str,
                        help='snulife user id')
    parser.add_argument('--password', '-p',
                        # required=True,
                        type=str,
                        help='snulife password')
    parser.add_argument('--sender', '-s',
                        type=str,
                        help='sender email address or gmail id')
    parser.add_argument('--gmail_password', '-gp',
                        type=str,
                        help='gmail account password if sender is gmail account')
    parser.add_argument('--receiver', '-r',
                        type=str,
                        help='receiver (ex. asd@asd.net,qwe@qwe.com)')
    parser.add_argument('--title', '-t',
                        type=str,
                        help='email subject')
    parser.add_argument('--url', '-l',
                        type=str,
                        help='target url')
    parser.add_argument('--filter', '-f',
                        type=str,
                        help='regex filter')
    parser.add_argument('--keep_running', '-k',
                        type=str2bool,
                        default=False,
                        help='target class name')
    parser.add_argument('--class_name', '-c',
                        type=str,
                        help='target class name')
    return vars(parser.parse_args())


def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def to_unicode(s):
    if isinstance(s, str):
        return s.decode('utf-8')
    else:
        return s


def main():
    args = get_args()
    # arguments
    user_id = args.get('user_id', SNULIFE_ACCOUNT)
    password = args.get('password', SNULIFE_PASSWORD)
    sender = args['sender'] or platform.node()
    gmail_password = args['password'] or ''
    receiver = [email.strip() for email in (args['receiver'] or '').split(',')]
    title = to_unicode(args['title'] or TITLE)
    url = args['url'] or SNULIFE_CONSTANT['target']
    regex = to_unicode(args['filter'] or '')
    keep_running = args['keep_running']
    class_name = args['class_name'] or SNULIFE_CONSTANT['post_class']

    snulife = Snulife(user_id, password)
    if keep_running:
        while(True):
            try:
                snulife.crawl(url=url, class_name=class_name, regex=regex)\
                    .noti(title=title, sender=sender, receiver=receiver, password=gmail_password)
                print 'sleep ...'
                sleep(5)
                print 'wake up !!!'
            except Exception as e:
                print 'fail'
                print e
                print 'sleep ...'
                sleep(60)
                print 'wake up !!!'
    else:
        snulife.crawl(url=url, class_name=class_name, regex=regex)\
            .send_email(title=title, sender=sender, receiver=receiver, password=gmail_password)


if __name__ == '__main__':
    main()

