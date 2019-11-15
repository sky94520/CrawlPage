import redis
from datetime import datetime
from CrawlPage.utils import date2str, str2date


class RedisClient(object):

    def __init__(self, **kwargs):
        self.redis = redis.StrictRedis(**kwargs, decode_responses=True)
        # 不存在process
        if not self.redis.exists('process'):
            self.cls_number = None
            self.initialize()
        else:
            arr = self.redis.hmget('process', ['cls_number', 'cur_page', 'total_count', 'cur_count', 'index'])
            self.cls_number, self.cur_page = arr[0], int(arr[1])
            self.total_count, self.cur_count, self.index = int(arr[2]), int(arr[3]), int(arr[4])
            if self.redis.hexists('process', 'date'):
                self.date = str2date(self.redis.hget('process', 'date'))
                self.days = int(self.redis.hget('process', 'days'))

    def initialize(self):
        self.cur_page, self.index = 1, 1
        self.cur_count, self.total_count, = 0, -1
        self.date, self.days = datetime(datetime.now().year, 1, 1), 366

        self.redis.hmset('process', {'cur_page': self.cur_page,
                                     'total_count': self.total_count,
                                     'cur_count': self.cur_count, 'index': self.index})

    def set_days(self, days):
        self.redis.hset('process', 'days', days)

    def set_date(self, date):
        self.date = date
        dateStr = date2str(date)
        self.redis.hset('process', 'date', dateStr)

    def inc_index(self):
        self.index += 1
        self.redis.hset('process', 'index', self.index)

    def inc_page(self):
        self.cur_page += 1
        self.redis.hset('process', 'cur_page', self.cur_page)

    def add_cur_count(self, count):
        self.cur_count += count
        self.redis.hset('process', 'cur_count', self.cur_count)

    def set_cur_count(self, count):
        self.cur_count = count
        self.redis.hset('process', 'cur_count', count)

    def set_cur_page(self, page):
        self.cur_page = page
        self.redis.hset('process', 'cur_page', page)

    def hexists(self, key):
        return self.redis.hexists('process', key)

    def set_total_count(self, count):
        self.total_count = count
        self.redis.hset('process', 'total_count', count)

    def is_using_date(self):
        # 是否启用日期
        return self.redis.hexists('process', 'date')

    @property
    def main_cls_number(self):
        return self.redis.hget('process', 'cls_number')

    @main_cls_number.setter
    def main_cls_number(self, cls_number):
        self.cls_number = cls_number
        self.redis.hset('process', 'cls_number', cls_number)

    def del_process(self):
        self.redis.delete('process')

    def pop_from_queue(self):
        # 不存在键或者尺寸为0
        if not self.redis.exists('queue') or self.redis.llen('queue') == 0:
            return
        main_cls_number = self.redis.lpop('queue')
        return main_cls_number

    def is_empty_in_queue(self):
        """检测队列中是否有主分类号"""
        return not self.redis.exists('queue') or self.redis.llen('queue') == 0

