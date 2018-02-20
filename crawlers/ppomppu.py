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

    def _get_htmls(self, url_infos):
        print('Crawling',
              f"from {', '.join(self.boards)}",
              f"having {', '.join(self.keywords)} ...",
              sep='\n\t', end=' ')
        resps = [request.urlopen(info.url) for info in url_infos]
        html_infos = []
        HtmlInfo = namedtuple('HtmlInfo', ['board', 'keyword', 'html'])
        for url_info, resp in zip(url_infos, resps):
            if resp.status != 200:
                continue
            text = resp.read()
            tree = html.fromstring(text)
            html_infos.append(HtmlInfo(url_info.board, url_info.keyword, tree))
        print('Done')
        return html_infos

    def _find(self, html_info, pattern):
        board, keyword, tree = html_info
        posts = []
        for e in tree.find_class('list_comment2'):
            title = e.getparent().getchildren()[0].text_content().strip()
            if not re.search(pattern, title):
                continue
            link = e.getparent().getchildren()[0].get('href').strip()
            find = re.findall(r'no=(\d+)', link)
            if not find:
                continue
            pid = find[-1]
            link = self.base_url.format(board=self.board_map[board], pid=pid)
            dt = e.getparent().getparent().getparent().getparent().getnext().get('title')
            posts.append(Post(pid, title, link, board, keyword, dt))
        return posts
