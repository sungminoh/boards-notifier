# -*- coding: utf-8 -*-

import argparse
import platform
from time import sleep
from crawlers.snulife import Snulife


GMAIL_ACCOUNT = '<account without @gmail.com>'
GMAIL_PASSWORD = '<password>'
SNULIFE_ACCOUNT = '<snulife account>'
SNULIFE_PASSWORD = '<snulife password>'
TITLE = u'스누라이프 알리미 입니다.'
SNULIFE_CONSTANT = {
    'post_class': 'hx',
    'target': 'http://snulife.com/housing/'
}


def get_args():
    description = 'snulife new post alarm'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--user_id', '-u', type=str,
                        help='snulife user id')
    parser.add_argument('--password', '-p', type=str,
                        help='snulife password')
    parser.add_argument('--sender', '-s', type=str,
                        help='sender email address or gmail id')
    parser.add_argument('--gmail_password', '-gp', type=str,
                        help='gmail account password if sender is gmail account')
    parser.add_argument('--receiver', '-r', type=str,
                        help='receiver (ex. asd@asd.net,qwe@qwe.com)')
    parser.add_argument('--title', '-t', type=str,
                        help='email subject')
    parser.add_argument('--url', '-l', type=str,
                        help='target url')
    parser.add_argument('--boards', type=str,
                        help='snulife boards')
    parser.add_argument('--keywords', type=str,
                        help='search keywords')
    parser.add_argument('--filter', '-f', type=str,
                        help='regex filter')
    parser.add_argument('--keep_running', '-k', type=str2bool, default=False,
                        help='target class name')
    parser.add_argument('--class_name', '-c', type=str,
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
    if isinstance(s, bytes):
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
                print('sleep ...')
                sleep(5)
                print('wake up !!!')
            except Exception as e:
                print('fail', e, 'sleep ...', sep='\n')
                sleep(60)
                print('wake up !!!')
            break
    else:
        snulife.crawl(url=url, class_name=class_name, regex=regex)\
            .noti(title=title, sender=sender, receiver=receiver, password=gmail_password)


if __name__ == '__main__':
    main()
