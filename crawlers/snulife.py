# -*- coding: utf-8 -*-
import grequests
import requests
from lxml import html
from itertools import chain
import pickle as pk
from datetime import datetime
import re
import os
from collections import namedtuple

from helpers import EmailHandler, DbManager

class Post(object):
    def __init__(self, id, title, url, board, keyword, dt):
        self.id = id
        self.title = title
        self.url = url
        self.board = board
        self.keyword = keyword
        self.dt = dt

    def __str__(self):
        return f'Post({self.__dict__})'

    def __repr__(self):
        return str(self)


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
        self.db = DbManager(__file__)
        self.db.create(('title', 'text'), ('url', 'text'), ('board', 'text'),
                       ('keyword', 'text'), ('dt', 'text'))
        self.session = requests.session()
        self.data['user_id'] = user_id
        self.data['password'] = password
        self.boards = None
        self.keywords = None
        self.posts = None
        self.new_posts = None

    def noti(self, title, sender, receiver, content='', password=''):
        if self.new_posts:
            content = self.__build_content(self.new_posts)
            print(content)
            EmailHandler.send_email(title, sender, receiver, content, password)
        else:
            print('No new posts')

    @staticmethod
    def __build_content(posts):
        def post2row(post):
            print(post.dt)
            dt = datetime.strptime(post.dt, '%Y.%m.%d %H:%M')
            if dt.hour == 0 and dt.minute == 0:
                dt = dt.strftime('%y.%m.%d')
            else:
                dt = dt.strftime('%H:%M')
            return str(f'''<tr><td style="text-align: center;">{dt}</td>
                       <td><a href={post.url}>{post.title}</a></td>
                       <td style="text-align: center;">{post.keyword}</td>
                       <td style="text-align: center;">{post.board}</td></tr>''')
        return str(f'''
                   <html>
                    <head></head>
                    <body>
                        <p>{datetime.now().strftime('%Y.%m.%d')} 스누라이프 새글입니다.</p></br>
                        <table style="width:100%">
                            <tr><th>게시일</th><th>제목</th><th>키워드</th><th>게시판</th></tr>
                            {''.join(map(post2row, posts))}
                        </table>
                    </body>
                   </html>''')

    def crawl(self, boards='', keywords='', regex=''):
        self.boards = [board.strip() for board in boards.split(',')]
        self.keywords = [keyword.strip() for keyword in keywords.split(',')]
        url_infos = self.__build_urls(self.boards, self.keywords)
        self.__connect()
        html_infos = self.__get_htmls(url_infos)
        posts = self.__find_all(html_infos, regex)
        self.posts = self.__groupByAppend(posts, ['id'], 'keyword')
        self.__save(self.posts)
        return self

    def __connect(self):
        self.session.post(self.login, self.data, headers=self.header)
        print('Session connected')
        return self

    @classmethod
    def __build_urls(cls, boards, keywords):
        UrlInfo = namedtuple('UrlInfo', ['board', 'keyword', 'url'])
        url_infos = []
        for board in map(lambda x: cls.board_map[x], boards):
            for keyword in keywords:
                url = cls.board_url.format(board=board, keyword=keyword)
                url_infos.append(UrlInfo(board, keyword, url))
        return url_infos

    def __get_htmls(self, url_infos):
        print('Crawling',
              f"from {', '.join(self.boards)}",
              f"having {', '.join(self.keywords)} ...",
              sep='\n\t', end=' ')
        reqs = [grequests.get(info.url, session=self.session) for info in url_infos]
        resps = grequests.map(reqs)
        html_infos = []
        HtmlInfo = namedtuple('HtmlInfo', ['board', 'keyword', 'html'])
        for url_info, resp in zip(url_infos, resps):
            if resp.status_code != 200:
                continue
            text = resp.text
            tree = html.fromstring(text)
            html_infos.append(HtmlInfo(url_info.board, url_info.keyword, tree))
        print('Done')
        return html_infos

    @staticmethod
    def __find_all(html_infos, regex=''):
        print("Finding posts containing '%s' ..." % (regex), end=' ')
        posts = []
        for board, keyword, tree in html_infos:
            for e in zip(tree.find_class('hx'), tree.find_class('time')):
                title = e[0].text_content().strip()
                if not re.search(regex, title):
                    continue
                link = e[0].values()[0].strip()
                find = re.findall('document_srl=(\d+)', link)
                if not find:
                    continue
                pid = find[0]
                dt = e[1].text_content().strip()
                if ':' in dt:
                    dt = datetime.strptime(datetime.now().strftime('%y.%m.%d ') + dt, '%y.%m.%d %H:%M')
                else:
                    dt = datetime.strptime(dt, '%y.%m.%d')
                dt = dt.strftime('%Y.%m.%d %H:%M')
                posts.append(Post(pid, title, link, board, keyword, dt))
        print('Done')
        return posts

    @staticmethod
    def __groupByAppend(data, keys, *fields):
        dic = dict()
        for d in data:
            g = tuple([getattr(d, k) for k in keys])
            if g not in dic:
                for f in fields:
                    setattr(d, f, set(getattr(d, f).split(',')))
                dic[g] = d
                continue
            for f in fields:
                getattr(dic[g], f).add(getattr(d, f))
        ret = dic.values()
        for d in ret:
            for f in fields:
                setattr(d, f, ','.join(getattr(d, f)))
        return ret

    def __save(self, posts):
        print('Saving posts ...')
        updated = 0
        inserted = 0
        self.new_posts = []
        for post in posts:
            print(f'[{post.dt}] {post.title} ...', end=' ')
            rows = self.db.select([{'id': post.id}])
            if rows:
                print('exists')
                keyword = rows[0][4].split(',') + post.keyword.split(',')
                post.keyword = ','.join(set(keyword))
                updated += 1
            else:
                print('new')
                self.new_posts.append(post)
                inserted += 1
        self.new_posts.sort(key=lambda p: p.dt)
        self.new_posts.reverse()
        self.db.insert(*[post.__dict__ for post in posts], force=True)
        print(f'updated: {updated}\ninserted: {inserted}')
