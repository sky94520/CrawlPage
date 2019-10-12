# -*- coding: utf-8 -*-
import os
import re
import redis
import scrapy
from urllib.parse import urlencode, urljoin, urlparse, parse_qsl

from CrawlPage.config import REDIS_CONFIG
from CrawlPage.items import PatentItem


class PageSpider(scrapy.Spider):
    name = 'page'
    # allowed_domains = ['baidu']
    # start_urls = ['http://baidu/']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 测试环境下使用数据库1
        SCRAPY_ENV = os.getenv('SCRAPY_ENV', 'development')
        REDIS_CONFIG['db'] = 1 if SCRAPY_ENV == 'development' else 0
        self.redis = redis.StrictRedis(**REDIS_CONFIG, decode_responses=True)
        # main_cls_number H04N1/62
        self.main_cls_number = 'A47J27/00'
        # 数字正则提取
        self.pattern = r'\d+(\,\d+)*'
        # cookie
        self.cookie_dirty = True
        self.cookie = None

    def start_requests(self):
        # 判断具体的个数
        yield self.create_request()

    def parse(self, response):
        """
        根据传来的response解析页面 同时并保存页面到本地
        如果出错，则会抛出异常
        :param response: scrapy返回的response
        :return: total_count 总个数, details [详情页 {"url": "", "title": ""}, ...]
        """
        # 判断个数有没有超过阈值 目前为6000 超过则更改日期，重新请求
        # 否则，则进行解析 yield item后再yield 下一页的request
        # 获取结果个数 若出现验证码则请求并重新更换cookie
        pager = response.xpath("//div[@class='pagerTitleCell']//text()").extract_first(None)
        if pager is None:
            self.cookie_dirty = True
            yield response.request
            return
        # 获取总个数
        total_count = self._get_page_number(pager)
        # 专利条目数组
        tr_list = response.xpath("//table[@class='GridTableContent']//tr")
        length = len(tr_list)
        # 这个分类的条目个数确实为0
        if length == 0 and total_count == 0:
            return None
        # 解析条目 去掉头
        for index in range(1, length):
            tr = tr_list[index]
            link = tr.xpath('./td[2]/a/@href').extract_first()
            parse_result = urlparse(link)
            query_tuple = parse_qsl(parse_result[4])

            item = PatentItem()
            for t in query_tuple:
                if t[0] in PatentItem.KEYS:
                    item[t[0]] = t[1]

            item['title'] = tr.xpath('./td[2]/a/text()').extract_first()
            yield item
        # TODO:
        return total_count

    def create_request(self, cur_page=1):
        """
        创建一个专利页面的请求
        :param cur_page: 要获取的页面
        :return: request
        """
        params = {
            'ID': None,
            'tpagemode': 'L',
            'dbPrefix': 'SCPD',
            'Fields': None,
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
        url = urljoin(base_url, urlencode(params))

        return scrapy.Request(url=url, callback=self.parse)

    def _get_page_number(self, num_str):
        # 正则提取，并转换成整型
        pager = re.search(self.pattern, num_str)
        pager = re.sub(',', '', pager.group(0))
        total_count = int(pager)
        return total_count
