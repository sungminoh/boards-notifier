# -*- coding: utf-8 -*-
from datetime import datetime
import re

from crawlers.crawler import Crawler, Post


class Snulife(Crawler):
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

    login_url = 'https://snulife.com/'
    board_url = 'https://snulife.com/?act=&vid=&mid={board}&category=&search_keyword={keyword}&search_target=title_content&page={page}'

    def __init__(self, user_id, password):
        super().__init__()
        self.data['user_id'] = user_id
        self.data['password'] = password
        self._connect()

    @staticmethod
    def _find(html_info, pattern):
        board, keyword, tree = html_info
        posts = []
        for e in zip(tree.find_class('hx'), tree.find_class('time')):
            title = e[0].text_content().strip()
            if not re.search(pattern, title):
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
            dt = dt.strftime('%Y.%m.%d %H:%M:%S')
            posts.append(Post(pid, title, link, board, keyword, dt))
        return posts
