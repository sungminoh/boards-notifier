# -*- coding: utf-8 -*-

import argparse
import platform
from time import sleep
from crawlers.snulife import Snulife
from crawlers.ppomppu import Ppomppu


GMAIL_ACCOUNT = '<account without @gmail.com>'
GMAIL_PASSWORD = '<password>'


def get_args():
    description = 'new post alarm'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--job', type=str, choices=['snulife', 'ppomppu'],
                        help='job [snulife]')
    parser.add_argument('--user_id', type=str, required=False,
                        help='site user id')
    parser.add_argument('--password', type=str, required=False,
                        help='site password')
    parser.add_argument('--sender', type=str, default='',
                        help='sender email address or gmail id')
    parser.add_argument('--gmail_password', type=str, default='',
                        help='gmail account password if sender is gmail account')
    parser.add_argument('--receivers', type=str, default=[], action='append',
                        help='receivers (ex. asd@asd.net,qwe@qwe.com)')
    parser.add_argument('--title', type=str, default='boards-notifier',
                        help='email subject')
    parser.add_argument('--content', type=str, default='new posts',
                        help='email content')
    parser.add_argument('--boards', type=str, default=[], action='append',
                        help='board name')
    parser.add_argument('--keywords', type=str, default=[], action='append',
                        help='search keywords')
    parser.add_argument('--n_pages', type=int, default=[], action='append',
                        help='number of pages to look over')
    parser.add_argument('--patterns', type=str, default=[], action='append',
                        help='regex pattern')
    parser.add_argument('--force', '-f', default=False, action='store_true',
                        help='notify though there is no new post')
    return parser.parse_args()


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
    if args.job == 'snulife':
        Snulife(args.user_id, args.password)\
            .crawl(boards=args.boards, keywords=args.keywords, patterns=args.patterns,
                   n_pages=args.n_pages, sync=True)\
            .noti(title=args.title, sender=args.sender, receivers=args.receivers,
                  content=args.content, password=args.gmail_password, force=args.force)
    elif args.job == 'ppomppu':
        Ppomppu()\
            .crawl(boards=args.boards, keywords=args.keywords, patterns=args.patterns,
                   n_pages=args.n_pages)\
            .noti(title=args.title, sender=args.sender, receivers=args.receivers,
                  content=args.content, password=args.gmail_password, force=args.force)


if __name__ == '__main__':
    main()
