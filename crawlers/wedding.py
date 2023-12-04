import json
import logging
from pprint import pprint
import requests
import argparse
from typing import List
import boto3
from lxml import html
from html.parser import HTMLParser


dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-2')
table = dynamodb.Table('cache')


# Set up logger
def get_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    # Create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    # Create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # Add formatter to console handler
    ch.setFormatter(formatter)
    # Add console handler to logger
    logger.addHandler(ch)
    return logger


logger = get_logger()


class WeddingCrawler:
    def __init__(self, ym):
        self.ym = ym
        self.cache = {}
        self.updated = {}
        self.load_cache()

    def load_cache(self):
        response = table.get_item(Key={'key': self.name, 'sort_key': self.name})
        data = response.get('Item', {}).get('data', '{}')
        self.cache = json.loads(data)
        logger.info(f'load_cache for {self.name}')

    def write_cache(self):
        response = table.put_item(Item={
            'key': self.name,
            'sort_key': self.name,
            'data': json.dumps(self.cache, ensure_ascii=False)})
        logger.info('write_cache\n%s', json.dumps(response, indent=2))

    def send_notification(self):
        url = 'https://maker.ifttt.com/trigger/wedding/json/with/key/<KEY>'
        requests.post(url, data=self.updated)


class EloungeCrawler(WeddingCrawler):
    name = 'elounge'
    def run(self):
        for _ym in self.ym:
            y, m = divmod(_ym, 100)
            resp = requests.post(
                f'https://eng.snu.ac.kr/enghouse_reserve?tab=3&year={y}&month={m}',
                data={'step': '2', 'reserve_type': 'w'})
            self.parse(html.fromstring(resp.content))

    def parse(self, response):
        # Now that we have access to the page, we can start scraping it
        # Extract the first table HTML object using XPath selectors
        table = response.xpath('//table')[1]
        # Extract the rows of the table
        rows = table.xpath('.//tr')
        # Extract the headers of the table (assuming the first row contains headers)
        headers = [header.strip() for header in rows[0].xpath('.//th/text()')]
        # Extract the data from each row of the table
        for row in rows[1:]:
            # Extract the data from each cell of the row
            cells = row.xpath('.//td')
            data = {}
            for index, cell in enumerate(cells):
                # Use the headers to create key-value pairs for the data
                data[headers[index]] = cell.xpath('.//text()')[0].strip()
            # Yield a JSON object with the extracted data
            logger.info(data)
            self.process_item(data)
        if self.updated:
            self.write_cache()
            self.send_notification()

    def process_item(self, data):
        if '토요일' in data.get('일자'):
            date = data.pop('일자')
            for k, v in data.items():
                key = f'{date} {k}'
                if self.cache.get(key) != v:
                    self.cache[key] = v
                    if v != '예약완료':
                        self.updated[key] = v
                else:
                    self.updated.pop(key, None)


class FacultyclubCrawler(WeddingCrawler):
    name = 'facultyclub'

    def run(self):
        for _ym in self.ym:
            y, m = divmod(_ym, 100)
            resp = requests.get(
                f'https://snufacultyclub.com/page.php?pgid=wedding4&year={y}&month={m}',
                headers={
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "accept-language": "en-US,en;q=0.9",
                    "cache-control": "no-cache",
                    "pragma": "no-cache",
                    "sec-ch-ua": "\"Microsoft Edge\";v=\"111\", \"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"111\"",
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": "\"macOS\"",
                    "sec-fetch-dest": "document",
                    "sec-fetch-mode": "navigate",
                    "sec-fetch-site": "none",
                    "sec-fetch-user": "?1",
                    "upgrade-insecure-requests": "1"
                },
                cookies={},  # Copy from a browser
            )
            self.parse(y, m, html.fromstring(resp.content))


    def parse(self, y, m, response):
        # Now that we have access to the page, we can start scraping it
        # Extract the first table HTML object using XPath selectors
        table = response.xpath('//table')[0]
        # Extract the rows of the table
        rows = table.xpath('.//tr')
        # Extract the headers of the table (assuming the first row contains headers)
        headers = [header.strip() for header in rows[0].xpath('.//th/text()')]
        # Extract the data from each row of the table
        for row in rows[1:]:
            # Extract the data from each cell of the row
            data = {}
            data[headers[0]] = f'{m}/' + row.xpath('.//th/span/text()')[0].strip()
            cells = row.xpath('.//td')
            for index, cell in enumerate(cells, 1):
                # Use the headers to create key-value pairs for the data
                data[headers[index]] = cell.xpath('.//span/@class')[0]
            # Yield a JSON object with the extracted data
            logger.info(data)
            self.process_item(data)
        if self.updated:
            self.write_cache()
            self.send_notification()

    def process_item(self, data):
        if '토' in data.get('일자'):
            date = data.pop('일자')
            for k, v in data.items():
                key = f'{date} {k}'
                if self.cache.get(key) != v:
                    self.cache[key] = v
                    if 'red' not in v:
                        self.updated[key] = v
                else:
                    self.updated.pop(key, None)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-ym', '--year-months', nargs='+', type=int, required=True)
    args = parser.parse_known_args()[0]
    EloungeCrawler(args.year_months).run()
    FacultyclubCrawler(args.year_months).run()


if __name__ == '__main__':
    main()
