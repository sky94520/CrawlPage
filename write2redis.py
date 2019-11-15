"""
把ipc分类从mongo中写入到redis中
"""
import os
from dotenv import load_dotenv
import xlrd

from CrawlPage.config import MONGO_CONFIG, REDIS_CONFIG
from CrawlPage.utils import MongoDB
from CrawlPage.RedisClient import RedisClient


def write_from_mongo(redis):
    CLS_PATTERN = os.getenv('CLS_PATTERN', 'A.{4,}')
    # 初始化mongo
    mongo = MongoDB(host=MONGO_CONFIG['ip'], port=MONGO_CONFIG['port'])
    mongo.authenticate(db_name=MONGO_CONFIG['database'], name=MONGO_CONFIG['username'],
                       password=MONGO_CONFIG['password'])

    db = mongo.get_db('patent')
    collection = db['ipc_category']
    # 获取到所有的A类别
    results = collection.find({'code': {'$regex': CLS_PATTERN}})
    cls_number_list = [result['code'] for result in results]
    # 写入
    redis.redis.rpush('queue', *cls_number_list)
    print('写入成功%d' % len(cls_number_list))


def write_from_xlsx(redis):
    filename = '2.xlsx'
    data = xlrd.open_workbook(filename)
    table = data.sheet_by_name('Sheet2')
    # 获取总行数
    rows = table.nrows
    col_values = table.col_values(0)
    print(col_values)
    redis.redis.rpush('queue', *col_values)
    print('写入成功%d' % len(col_values))


def main():
    # 初始化redis
    REDIS_DB = int(os.getenv('REDIS_DB', 4))
    REDIS_CONFIG['db'] = REDIS_DB
    redis = RedisClient(**REDIS_CONFIG)

    write_from_xlsx(redis)


if __name__ == '__main__':
    # 加载.env配置文件
    load_dotenv()
    main()
