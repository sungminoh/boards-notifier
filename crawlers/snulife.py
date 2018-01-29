# -*- coding: utf-8 -*-
import grequests
import requests
from lxml import html
from itertools import chain
import pickle as pk
from datetime import datetime
import re
import os

from helpers import EmailHandler


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

    login = 'https://snulife.com/'
    board_url = 'https://snulife.com/?act=&vid=&mid={board}&category=&search_keyword={keyword}

    def __init__(self, user_id, password):
        self.s = requests.session()
        self.data['user_id'] = user_id
        self.data['password'] = password

    def connect(self):
        self.s.post(self.login, self.data, headers=self.header)
        print('Session connected')
        return self

    def get(self, url):
        print('Crawl from urls below.', url, sep='\n')
        urls = url.split('\n') if isinstance(url, str) else url
        reqs = [grequests.get(i, session=self.s) for i in urls]
        resps = grequests.map(reqs)
        texts = [resp.text for resp in resps if resp.status_code == 200]
        self.trees = [html.fromstring(text) for text in texts]
        print('Crawl finished')
        return self

    def load_saved(self):
        ret = []
        if os.path.isfile(Snulife.saved):
            with open(Snulife.saved, 'rb') as f:
                ret = pk.load(f)
        return ret

    def find_all(self, class_name, regex=''):
        print("Finding all classname:%s containing '%s' ..." % (class_name, regex),
              end='')
        self.posts = []
        for tree in self.trees:
            for e in tree.find_class(class_name):
                link = e.values()[0]
                title = e.text_content().strip()
                if not re.search(regex, title):
                    continue
                self.posts.append((title, link))
        print('Done')
        return self

    def noti(self, title, sender, receiver, content='', password=''):
        print('Crawled posts', '\n'.join(chain(*self.posts)), sep='\n')
        saved = self.load_saved()
        if saved == self.posts:
            print('No new post')
        else:
            print('Got new post')
            with open(Snulife.saved, 'wb') as f:
                pk.dump(self.posts, f)
            new_posts = [p for p in self.posts if p not in saved]
            print('New posts', '\n'.join(chain(*new_posts)), sep='\n')
            EmailHandler.send_email(title, sender, receiver, content, password)

    def build_urls(boards='', keywords=''):
        urls = []
        for board in map(lambda x: x.strip(), boards.split(',')):
            for keyword in map(lambda x: x.strip(), keywords.split(',')):
                urls.append(self.board_url.format(board=board, keyword=keyword))
        return urls

    def crawl(self, boards='', keywords='', class_name='', regex=''):
        urls = self.build_urls(boards, keywords)
        self.connect().get(url).find_all(class_name, regex)
        return self