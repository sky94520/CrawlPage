# --coding:UTF-8--
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from dotenv import load_dotenv

import os
import logging
from CrawlPage.RedisClient import RedisClient
from CrawlPage.config import REDIS_CONFIG


def start_spider(redis):
    # 爬取使用的spider名称
    spider_name = 'page'
    project_settings = get_project_settings()
    settings = dict(project_settings.copy())
    # 合并配置
    process = CrawlerProcess(settings)
    # 启动爬虫
    params = {
        'redis': redis,
    }
    process.crawl(spider_name, **params)
    process.start(stop_after_crawl=False)


def main():
    # 加载.env配置文件
    load_dotenv()
    # 测试环境下使用数据库4
    queue = ['H04N1/62', 'a47j27/00']
    SCRAPY_ENV = os.getenv('SCRAPY_ENV', 'development')
    REDIS_CONFIG['db'] = 4 if SCRAPY_ENV == 'development' else 3
    redis = RedisClient(**REDIS_CONFIG)
    # 循环判断
    while len(queue) > 0:
        if redis.hexists('cls_number'):
            main_cls_number = redis.get_main_cls_number()
        else:
            main_cls_number = queue[0]
            queue.pop(0)
            redis.set_main_cls_number(main_cls_number)
            redis.initialize()
        # 爬取
        start_spider(redis)
        logging.info('主分类号%s爬取完成' % main_cls_number)
        # 删除缓存
        redis.del_process()


if __name__ == '__main__':
    main()
