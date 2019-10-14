import redis
from datetime import datetime
from CrawlPage.utils import date2str, str2date


class RedisClient(object):

    def __init__(self, cls_number, **kwargs):
        self.redis = redis.StrictRedis(**kwargs, decode_responses=True)
        # 不存在process
        if not self.redis.exists('process'):
            self.cur_page, self.index = 1, 1
            self.cur_count, self.total_count, = 0, -1
            self.date, self.days = datetime(datetime.now().year, 1, 1), 366

            self.redis.hmset('process', {'cls_number': cls_number, 'cur_page': self.cur_page,
                                         'total_count': self.total_count,
                                         'cur_count': self.cur_count, 'index': self.index})
        else:
            arr = self.redis.hmget('process', ['cur_page', 'total_count', 'cur_count', 'index'])
            self.cur_page, self.total_count, self.cur_count, self.index = int(arr[0]), int(arr[1]), int(arr[2]), int(arr[3])
            if self.redis.hexists('process', 'date'):
                self.date = str2date(self.redis.hget('process', 'date'))
                self.days = int(self.redis.hget('process', 'days'))

    def set_days(self, days):
        self.redis.hset('process', 'days', days)

    def set_date(self, date):
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
