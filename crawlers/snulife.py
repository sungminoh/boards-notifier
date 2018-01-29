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
    saved = 'cache/snulife.pkl'

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

    board_map = {
        '자유게시판': 'gongsage',
        '사랑방': 'love',
        '서울대광장': 'snuplaza',
        '재테크': 'invest',
        '스누지식인': 'snukin',
        '학부생라운지': 'student',
        '원생라운지': 'postgraduate',
        '졸업생라운지': 'graduate',
        'Global Lounge': 'global',
        '동아리홍보': 'clubad',
        '교내행사홍보': 'schoolad',
        '독강게시판': 'lecture_community',
        '강의교환': 'lecture_exchange',
        '족보요청': 'lecture_exam_want',
        '취업게시판': 'career_board',
        '고시게시판': 'examination',
        '유학게시판': 'abroad',
        '전문대학원': 'gradschool',
        '창업게시판': 'foundation',
        '스터디게시판': 'study',
        '학과정보': 'major_board',
        '벼룩시장': 'market',
        '제휴이벤트': 'event',
        '스누복덕방': 'housing',
        '교재4989': 'book',
        '분실물찾기': 'lostfound',
        '과외구하기': 'lesson',
        '구인게시판': 'partjob',
        '맛집제보하기': 'gourmet_recommend',
    }

    login = 'https://snulife.com/'
    board_url = 'https://snulife.com/?act=&vid=&mid={board}&category=&search_keyword={keyword}&search_target=title_content'

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

    def build_urls(self, boards='', keywords=''):
        urls = []
        for board in map(lambda x: self.board_map[x.strip()], boards.split(',')):
            for keyword in map(lambda x: x.strip(), keywords.split(',')):
                urls.append(self.board_url.format(board=board, keyword=keyword))
        return urls

    def crawl(self, boards='', keywords='', class_name='', regex=''):
        urls = self.build_urls(boards, keywords)
        self.connect().get(urls).find_all(class_name, regex)
        return self
