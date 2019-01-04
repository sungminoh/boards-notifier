# -*- coding: utf-8 -*-
from datetime import datetime
from urllib import request, parse
from lxml import html
import re
from collections import namedtuple

from crawlers.crawler import Crawler, Post


class Ppomppu(Crawler):
    board_map = {
        '뽐뿌게시판': 'ppomppu',
        '해외뽐뿌': 'ppomppu4',
        '쿠폰게시판': 'coupon',
        '이벤트게시판': 'event',
        '모바일이벤트': 'mobile'
    }

    base_url = 'http://www.ppomppu.co.kr/zboard/view.php?id={board}&no={pid}'
    board_url = 'http://www.ppomppu.co.kr/zboard/zboard.php?id={board}&page={page}&search_type=sub_memo&keyword={keyword}'

    def __init__(self):
        super().__init__()

    def _find(self, html_info, pattern):
        board, keyword, tree = html_info
        posts = []
        for e in tree.find_class('list_comment2'):
            elements = e.getparent().getchildren();
            title_components = re.findall(r'/images/menu/(\w+)_', elements[0].get('src') or '')
            title_components.append(elements[-2].text_content().strip())
            title = ' '.join(title_components)
            if not title or not re.search(pattern, title):
                continue
            hyper_link = e.getprevious().get('href')
            find = re.findall(r'no=(\d+)', hyper_link)
            if not hyper_link or not find:
                continue
            pid = find[-1]
            link = self.base_url.format(board=self.board_map[board], pid=pid)
            dt = '20' + e.getparent().getparent().getparent().getparent().getnext().get('title')
            posts.append(Post(pid, title, link, board, keyword, dt))
        return posts
