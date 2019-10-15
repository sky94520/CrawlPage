# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import logging
import requests
from datetime import timedelta, datetime
from scrapy.downloadermiddlewares.retry import RetryMiddleware
import proxy_pool
from CrawlPage.utils import date2str


logger = logging.getLogger(__name__)


class RetryOrErrorMiddleware(RetryMiddleware):
    """在之前的基础上增加了一条判断语句，当重试次数超过阈值时，发出错误"""

    def _retry(self, request, reason, spider):
        # 获取当前的重试次数
        retry_times = request.meta.get('retry_times', 0) + 1
        # 最大重试次数
        max_retry_times = self.max_retry_times
        if 'max_retry_times' in request.meta:
            max_retry_times = request.meta['max_retry_times']

        # 超出最大 直接报错即可
        if retry_times > max_retry_times:
            logger.error('%s %s retry times beyond the bounds' % (request.url, spider.main_cls_number))
        super()._retry(request, reason, spider)


class ProxyMiddleware(object):

    def process_request(self, request, spider):
        # 最大重试次数
        retry_times = request.meta.get('retry_times', 0)
        max_retry_times = spider.crawler.settings.get('MAX_RETRY_TIMES')
        proxy = proxy_pool.get_random_proxy()
        # 最后一次尝试不使用代理
        if proxy and retry_times != max_retry_times:
            logger.info('使用代理%s' % proxy)
            request.meta['proxy'] = 'http://%s' % proxy
        else:
            reason = '代理获取失败' if proxy else ('达到最大重试次数[%d/%d]' % (retry_times, max_retry_times))
            logger.warning('%s，使用自己的IP' % reason)


class CookieMiddleware(object):

    def process_request(self, request, spider):
        # 重新请求cookie
        if spider.cookie_dirty:
            params = {}
            # 添加年份
            if spider.redis.is_using_date():
                params = self._get_year_bound(spider.date, spider.days)
            # 死循环获取cookie
            cookie = None
            while not cookie:
                cookie = self.get_cookie(cls_number=spider.main_cls_number, **params)
                logger.warning('获取cookie %s' % cookie)
            spider.cookie = cookie
            spider.cookie_dirty = False
        # 赋值cookie
        request.headers['Cookie'] = spider.cookie

    def get_cookie(self, cls_number, code='*', proxies=None, **kwargs):
        """
        根据条件给知网发送post请求来获取对应的cookie
        :param cls_number: 主分类号
        :param code: 条件，知网会根据条件来进行搜索
        :param proxies: 代理 proxies = {'http': 'host:port', 'https': 'host:port'}
        :return: cookie 字符串类型，主要用于赋值到header中的Cookie键
        headers = {'Cookie': cookie}
        """
        params = {
            "action": "",
            "NaviCode": code,
            "ua": "1.21",
            "isinEn": "0",
            "PageName": "ASP.brief_result_aspx",
            "DbPrefix": "SCPD",
            "DbCatalog": "中国专利数据库",
            "ConfigFile": "SCPD.xml",
            "db_opt": "SCOD",
            "db_value": "中国专利数据库",
            "txt_1_sel": "CLZ$=|?",
            "txt_1_value1": cls_number,
            "txt_1_relation": "#CNKI_AND",
            "txt_1_special1": "=",
            "his": 0,
            "__": self._get_now_gmt_time()
        }
        params.update(**kwargs)
        url = 'http://kns.cnki.net/kns/request/SearchHandler.ashx'
        try:
            response = requests.post(url, params=params, proxies=proxies)
            cookies = requests.utils.dict_from_cookiejar(response.cookies)

            cookie_str = ""
            for key in cookies:
                value = cookies[key]
                text = "%s=%s;" % (key, value)
                cookie_str += text

            return cookie_str
        except Exception as e:
            print(e)
        return None

    def _get_now_gmt_time(self):
        """
        获取当前的中国标准时间，主要用于赋值给form data
        :return: 当前的时间字符串
        """
        GMT_FORMAT = '%a %b %d %Y %H:%M:%S GMT+0800'
        now = datetime.utcnow() + timedelta(hours=8)
        text = '%s (中国标准时间)' % now.strftime(GMT_FORMAT)

        return text

    def _get_year_bound(self, date, days):
        params = {}
        if date is None:
            return params

        params['date_gkr_from'] = date2str(date)
        ret = False
        if days:
            old_year = date.year
            to = date + timedelta(days=days)
            if to.year != old_year:
                ret = True
        if days is None or ret:
            to = datetime(date.year, 12, 31)
        params['date_gkr_to'] = date2str(to)
        return params


