# -*- coding: utf-8 -*-
import os
import re
import scrapy
from urllib.parse import urlencode, urlparse, parse_qsl
from datetime import datetime, timedelta

from CrawlPage.config import REDIS_CONFIG
from CrawlPage.items import PatentItem
from CrawlPage.RedisClient import RedisClient
from CrawlPage.utils import date2str


class IdentifyingCodeError(Exception):
    """出现验证码所引发的异常"""
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text


class PageSpider(scrapy.Spider):
    name = 'page'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # main_cls_number H04N1/62
        self.main_cls_number = 'A47J27/00'
        # 测试环境下使用数据库4
        SCRAPY_ENV = os.getenv('SCRAPY_ENV', 'development')
        REDIS_CONFIG['db'] = 4 if SCRAPY_ENV == 'development' else 3
        self.redis = RedisClient(self.main_cls_number, **REDIS_CONFIG)
        # 数字正则提取
        self.pattern = r'\d+(\,\d+)*'
        # cookie
        self.cookie_dirty, self.cookie = True, None
        self.equal_count = 0

    def start_requests(self):
        # 判断具体的个数
        yield self.create_request()

    def parse(self, response):
        """
        从页面提取数据并进行处理
        :param response:
        :return:
        """
        try:
            self.logger.info('正在爬取%s: 第%d页' % (self.main_cls_number, self.redis.cur_page))
            result = self.parse_page(response)
            if result is None:
                return
            # 超过阈值 缩小范围
            total_count = result['total_count']
            if total_count > 6000:
                if self.redis.total_count == -1:
                    self.redis.set_total_count('total_count')
                if self.redis.is_using_date():
                    self.redis.set_days(self.redis.days // 2)
                else:
                    self.redis.set_days(self.redis.days)
                self.logger.warning('页面数据%d个，尝试改为%d天爬取' % (total_count, self.redis.days))
                self.redis.set_date(self.redis.date)
                self.cookie_dirty = True
                yield self.create_request(self.redis.cur_page)
                return
            # 返回items
            item = result['item']
            yield item
            # 这一页爬取完成
            old_count = self.redis.cur_count
            # 更新值
            self.redis.inc_index()
            self.redis.add_cur_count(count=len(item['array']))
            self.logger.info('爬取%s: 第%d页%d条，当前共%d条' %
                             (self.main_cls_number, self.redis.cur_page, len(item['array']), self.redis.cur_count))
            self.redis.inc_page()
            # 使用到了天数且爬取完成
            is_next = self.redis.cur_count < result['total_count']
            if not is_next and self.redis.is_using_date():
                is_next = True
                self.cookie_dirty = True
                self.redis.set_cur_page(1)
                self.redis.set_cur_count(0)
                # 年份处理
                old_year = self.redis.date.year
                self.redis.date = self.redis.date + timedelta(days=self.redis.days)
                # 超出年份, 切换到下一年
                if self.redis.date.year != old_year:
                    self.redis.date = datetime(old_year-1, 1, 1)
                    self.redis.set_days(366)
                self.redis.set_date(self.redis.date)
                self.logger.info('爬取从%s开始' % date2str(self.redis.date))
            # 页面爬取完成但未发现数据，计数
            self.equal_count = 0 if old_count != self.redis.cur_count else self.equal_count + 1
            # is_next 表示继续爬取页面 equal_count 表示连续数次以上item个数未发生变化
            if is_next and self.equal_count < 4:
                yield self.create_request(self.redis.cur_page)
        # 出现验证码 重新请求
        except Exception as e:
            self.logger.error(e)
            self.cookie_dirty = True
            yield response.request

    def parse_page(self, response):
        """
        单纯地解析页面结构 如果页面发生问题则抛出异常，否则返回一个字典
        :param response:
        :return: 返回None表示确实没有数据 否则返回 dict{'total_count': int, 'items': []}
        """
        pager = response.xpath("//div[@class='pagerTitleCell']//text()").extract_first(None)
        # 爬取页面结构失败，则报错
        if pager is None:
            raise IdentifyingCodeError('%s出现验证码' % self.main_cls_number)
        # TODO:判断个数有没有超过阈值 目前为6000 超过则更改日期，重新请求
        total_count = self._get_page_number(pager)
        # 专利条目数组
        tr_list = response.xpath("//table[@class='GridTableContent']//tr")
        length = len(tr_list)
        # 这个分类的当前页面条目个数确实为0 爬取完成
        if length == 0 and total_count == 0:
            return None
        item = PatentItem()
        item['response'] = response
        item['array'] = []
        # 解析条目 去掉头
        for index in range(1, length):
            tr = tr_list[index]
            link = tr.xpath('./td[2]/a/@href').extract_first()
            parse_result = urlparse(link)
            query_tuple = parse_qsl(parse_result[4])
            datum = {}

            for t in query_tuple:
                if t[0] in PatentItem.KEYS:
                    datum[t[0]] = t[1]
            datum['title'] = tr.xpath('./td[2]/a/text()').extract_first()
            item['array'].append(datum)

        return {
            'total_count': total_count,
            'item': item
        }

    def create_request(self, cur_page=1):
        """
        创建一个专利页面的请求
        :param cur_page: 要获取的页面
        :return: request
        """
        params = {
            'ID': '',
            'tpagemode': 'L',
            'dbPrefix': 'SCPD',
            'Fields': '',
            'DisplayMode': 'listmode',
            'PageName': 'ASP.brief_result_aspx',
            'isinEn': 0,
            'QueryID': 3,
            'sKuaKuID': 3,
            'turnpage': 1,
            'RecordsPerPage': self.settings.get('PATENT_NUMBER_PER_PAGE', 50),
            'curpage': cur_page,
        }
        base_url = 'http://kns.cnki.net/KNS/brief/brief.aspx'
        url = '%s?%s' % (base_url, urlencode(params))
        meta = {
            'index': self.redis.index,
            'max_retry_times': self.crawler.settings.get('MAX_RETRY_TIMES')
        }
        return scrapy.Request(url=url, callback=self.parse, meta=meta, dont_filter=True)

    def _get_page_number(self, num_str):
        # 正则提取，并转换成整型
        pager = re.search(self.pattern, num_str)
        pager = re.sub(',', '', pager.group(0))
        total_count = int(pager)
        return total_count

