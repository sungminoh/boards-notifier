# -*- coding: utf-8 -*-
import grequests
import requests
from urllib import request, parse
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
        self.id = str(id)
        self.title = title
        self.url = url
        self.board = board
        self.keyword = keyword
        self.dt = dt

    def __str__(self):
        return f'Post({self.__dict__})'

    def __repr__(self):
        return str(self)

    def __eq__(self, post):
        return self.id == post.id and self.title == self.title and self.url == self.url


class Crawler(object):
    data = {}
    header = {}
    board_map = {}
    login_url = 'http://<login url, this can be null or empty string>'
    board_url = 'http://<board url with placeholder for board, keyword and page>'

    def __init__(self):
        self.db = DbManager(self.__class__.__name__.lower())
        self.db.create(('title', 'text'), ('url', 'text'), ('board', 'text'),
                       ('keyword', 'text'), ('dt', 'text'))
        self.session = requests.session()
        self.boards = []
        self.keywords = []
        self.posts = []
        self.new_posts = []
        self.failed_url_infos = []

    def noti(self, title, sender, receiver, content='', password='', force=False):
        if force or self.new_posts:
            contents = [content] + ['FAIL: %s, %s (%s)' % tup for tup in self.failed_url_infos]
            if not self.new_posts:
                contents.append('No new posts')
            html_content = self.__build_content(self.new_posts, contents=contents)
            EmailHandler.send_email(title, sender, receiver, html_content, password)
        else:
            print('No new posts')

    @staticmethod
    def __build_content(posts, contents=None):
        def content2html(content):
            return str(f'<p>{content}</p>')
        def post2html(post):
            dt = datetime.strptime(post.dt, '%Y.%m.%d %H:%M:%S')
            if dt.hour == 0 and dt.minute == 0 and dt.second == 0:
                dt = dt.strftime('%y.%m.%d')
            else:
                dt = dt.strftime('%y.%m.%d %H:%M')
            return str(f'''<tr><td style="text-align: center;">{dt}</td>
                       <td><a href={post.url}>{post.title}</a></td>
                       <td style="text-align: center;">{post.keyword}</td>
                       <td style="text-align: center;">{post.board}</td></tr>''')
        return str(f'''
                   <html>
                    <head></head>
                    <body>
                        <p>{datetime.now().strftime('%Y.%m.%d')}</p></br>
                        {''.join(map(content2html, contents))}
                        <table style="width:100%">
                            <tr><th>게시일</th><th>제목</th><th>키워드</th><th>게시판</th></tr>
                            {''.join(map(post2html, posts))}
                        </table>
                    </body>
                   </html>''')

    def crawl(self, boards='', keywords='', n_pages=1, pattern='', sync=False):
        self.boards = [board.strip() for board in boards.split(',')]
        self.keywords = [keyword.strip() for keyword in keywords.split(',')]
        url_infos = self.__build_urls(self.boards, self.keywords, n_pages)
        html_infos = self._get_htmls(url_infos, sync=sync)
        posts = self.__find_all(html_infos, pattern)
        self.posts = self.__groupByAppend(posts, ['id'], 'keyword')
        self.__save(self.posts)
        return self

    def _connect(self):
        self.session.post(self.login_url, self.data, headers=self.header)
        print('Session connected')
        return self

    @classmethod
    def __build_urls(cls, boards, keywords, n_pages):
        UrlInfo = namedtuple('UrlInfo', ['board', 'keyword', 'url'])
        url_infos = []
        for board, board_name in map(lambda x: (cls.board_map[x], x), boards):
            for keyword in keywords:
                for page in range(1, 1+n_pages):
                    url = cls.board_url.format(board=board,
                                               keyword=parse.quote_plus(keyword),
                                               page=page)
                    url_infos.append(UrlInfo(board_name, keyword, url))
        return url_infos

    def _get_htmls(self, url_infos, sync):
        print('Crawling',
              f"from {', '.join(self.boards)}",
              f"having {', '.join(self.keywords)} ...",
              sep='\n\t', end=' ')
        resps = [None for _ in url_infos]
        if sync:
            print('')
            for i, info in enumerate(url_infos):
                print('FETCHING: %s, %s, (%s)' % info)
                resps[i] = self.session.get(info.url)
        else:
            resps = grequests.map([grequests.get(info.url, session=self.session)
                                   for info in url_infos])
        html_infos = []
        HtmlInfo = namedtuple('HtmlInfo', ['board', 'keyword', 'html'])
        for url_info, resp in zip(url_infos, resps):
            if resp is None or resp.status_code != 200:
                status = 'None' if resp is None else resp.status_code
                print(f'FAIL({status}): %s, %s (%s)' % url_info)
                self.failed_url_infos.append(url_info)
                continue
            text = resp.text
            tree = html.fromstring(text)
            html_infos.append(HtmlInfo(url_info.board, url_info.keyword, tree))
        print('Done')
        return html_infos

    def __find_all(self, html_infos, pattern=''):
        print("Finding posts containing '%s' ..." % (pattern), end=' ')
        posts = []
        for html_info in html_infos:
            posts.extend(self._find(html_info, pattern))
        print('Done')
        return posts

    @staticmethod
    def _find(html_info, pattern):
        board, keyword, tree = html_info
        # Parse tree here
        pid, title, link, dt = 0, '<post title>', 'http://<post link>', '<post dt>'
        posts = [Post(pid, title, link, board, keyword, dt)]
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
        exists = 0;
        updated = 0
        inserted = 0
        self.new_posts = []
        for post in posts:
            print(f'[{post.dt}] {post.title} ...', end=' ')
            rows = self.db.select([{'id': post.id}])
            if rows:
                if Post(*rows[0]) == post:
                    print('exists')
                    keyword = rows[0][4].split(',') + post.keyword.split(',')
                    post.keyword = ','.join(set(keyword))
                    exists += 1
                else:
                    print('updated')
                    self.new_posts.append(post)
                    updated += 1
            else:
                print('new')
                self.new_posts.append(post)
                inserted += 1
        self.new_posts.sort(key=lambda p: p.dt)
        self.new_posts.reverse()
        self.db.insert(*[post.__dict__ for post in posts], force=True)
        print(f'exists: {exists}\nupdated: {updated}\ninserted: {inserted}')
