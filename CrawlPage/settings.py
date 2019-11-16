# -*- coding: utf-8 -*-

# Scrapy settings for CrawlPage project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import os
import logging
import datetime

BOT_NAME = 'CrawlPage'

SPIDER_MODULES = ['CrawlPage.spiders']
NEWSPIDER_MODULE = 'CrawlPage.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'CrawlPage (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

BASEDIR = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))
# 最大重试次数
MAX_RETRY_TIMES = 20
# 每个页面的专利个数
PATENT_NUMBER_PER_PAGE = 50
# 日志格式化输出
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
# 日期格式
DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
NAME_FORMAT = "%H-%M-%S"

now = datetime.datetime.now()
filepath = os.path.join(BASEDIR, 'log', now.strftime("%Y-%m-%d"))

if not os.path.exists(filepath):
    os.makedirs(filepath)
# 存入文件
filename = os.path.join(filepath, "%s.txt" % now.strftime("%H-%M-%S"))
fp = logging.FileHandler(filename, "w", encoding="utf-8")
fp.setLevel(logging.INFO)

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT, handlers=[fp])

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'CrawlPage.middlewares.RetryOrErrorMiddleware': 550,
    'CrawlPage.middlewares.ProxyMiddleware': 843,
    'CrawlPage.middlewares.CookieMiddleware': 844,
}
# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'CrawlPage.pipelines.JsonPipeline': 300,
    'CrawlPage.pipelines.SavePagePipeline': 301,
}

# 禁止重定向
REDIRECT_ENALBED = False
# 允许出现404 403
HTTPERROR_ALLOWED_CODES = [404, 403, 401]
# 下载限制15秒为延时 默认180s
DOWNLOAD_TIMEOUT = 15
