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
        # 使用redis哪个db
        REDIS_DB = int(os.getenv('REDIS_DB', 4))
        REDIS_CONFIG['db'] = REDIS_DB
        self.redis = RedisClient(**REDIS_CONFIG)
        # 数字正则提取
        self.pattern = r'\d+(\,\d+)*'
        # cookie
        self._cookie_dirty, self._cookie = True, None

    def start_requests(self):
        # 存在断点
        if self.redis.hexists('cls_number'):
            request = self._create_request()
        # 不存在则尝试获取新的请求
        else:
            request = self._pop_new_request()
        # 判断具体的个数
        self.logger.info('开始爬取%s' % self.main_cls_number)
        if request:
            yield request

    def parse(self, response):
        """
        从页面提取数据并进行处理
        :param response:
        :return:
        """
        self.logger.info('正在爬取%s: 第%d页' % (self.redis.main_cls_number, self.redis.cur_page))
        try:
            result = self.parse_page(response)
        # 出现验证码 重新请求
        except IdentifyingCodeError as e:
            self.logger.error(e)
            self._cookie_dirty = True
            yield self._create_request(self.redis.cur_page)
            return
        # 返回None表示此类爬取完成 尝试开启新的请求并爬取
        if result is None and self.redis.having_cls_number_in_queue():
            yield self._pop_new_request()
            return
        # 超过阈值 缩小范围
        total_count = result['total_count']
        if self.redis.total_count == -1:
            self.redis.set_total_count(total_count)
        request = self._beyond_bounds(total_count)
        if request:
            yield request; return
        # 返回items
        yield result['item']
        # 这一页爬取完成
        is_next = self._crawl_page_done(total_count, result['item'])
        # 继续爬取
        if is_next:
            yield self._create_request(self.redis.cur_page)
        # 尝试创建新的请求
        elif self.redis.having_cls_number_in_queue():
            yield self._pop_new_request()
            return

    def parse_page(self, response):
        """
        单纯地解析页面结构 如果页面发生问题则抛出异常，否则返回一个字典
        :param response:
        :return: 返回None表示确实没有数据 否则返回 dict{'total_count': int, 'items': []}
        """
        pager = response.xpath("//div[@class='pagerTitleCell']//text()").extract_first(None)
        # 爬取页面结构失败，则报错
        if pager is None:
            raise IdentifyingCodeError('%s出现验证码' % self.redis.main_cls_number)
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
            # 键值对 映射
            for t in query_tuple:
                if t[0] in PatentItem.KEYS:
                    datum[t[0]] = t[1]
            datum['title'] = tr.xpath('./td[2]/a/text()').extract_first()
            item['array'].append(datum)

        return {
            'total_count': total_count,
            'item': item
        }

    def _create_request(self, cur_page=1):
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

    def _beyond_bounds(self, total_count):
        """判断是否超过界限，是的话则返回request"""
        if total_count > 6000:
            if self.redis.is_using_date():
                self.redis.set_days(self.redis.days // 2)
            else:
                self.redis.set_days(self.redis.days)
            self.logger.warning('页面数据%d个，尝试改为%d天爬取' % (total_count, self.redis.days))
            self.redis.set_date(self.redis.date)
            self._cookie_dirty = True
            return self._create_request(self.redis.cur_page)

    def _pop_new_request(self):
        """查看redis队列中是否有分类号，有则返回请求"""
        self._cookie_dirty = True
        self.redis.del_process()
        main_cls_number = self.redis.pop_main_cls_number()
        if main_cls_number:
            self.redis.main_cls_number = main_cls_number
            self.redis.initialize()
            return self._create_request(self.redis.cur_page)

    def _crawl_page_done(self, total_count, item):
        """爬取页面完成后的操作"""
        # 更新值
        self.redis.inc_index()
        self.redis.add_cur_count(count=len(item['array']))
        self.logger.info('爬取%s: 第%d页%d条，当前共%d条' % (self.redis.main_cls_number,
                                                   self.redis.cur_page, len(item['array']), self.redis.cur_count))
        self.redis.inc_page()
        # 使用到了天数且爬取完成
        is_next = self.redis.cur_count < total_count
        if not is_next and self.redis.is_using_date():
            is_next = True
            self._cookie_dirty = True
            self.redis.set_cur_page(1)
            self.redis.set_cur_count(0)
            # 年份处理
            old_year = self.redis.date.year
            date = self.redis.date + timedelta(days=self.redis.days)
            # 超出年份, 切换到下一年
            if date.year != old_year:
                # 最低年限，超出这个年限则不再进行爬取
                BOUND_YEAR = os.getenv('BOUND_YEAR', 1989)
                if BOUND_YEAR > old_year - 1:
                    is_next = False
                else:
                    date = datetime(old_year - 1, 1, 1)
                    self.redis.set_days(366)
            self.redis.set_date(date)
            self.logger.info('爬取从%s开始' % date2str(self.redis.date))
        # 是否继续爬取页面
        return is_next

    def _get_page_number(self, num_str):
        # 正则提取，并转换成整型
        pager = re.search(self.pattern, num_str)
        pager = re.sub(',', '', pager.group(0))
        total_count = int(pager)
        return total_count

    @property
    def main_cls_number(self):
        return self.redis.main_cls_number

    @property
    def date(self):
        return self.redis.date

    @property
    def days(self):
        return self.redis.days

    @property
    def cookie(self):
        return self._cookie

    @cookie.setter
    def cookie(self, cookie):
        self._cookie = cookie
        self._cookie_dirty = False

    @property
    def cookie_dirty(self):
        return self._cookie_dirty
