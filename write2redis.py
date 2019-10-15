"""
把ipc分类从mongo中写入到redis中
"""
import os
from dotenv import load_dotenv

from CrawlPage.config import MONGO_CONFIG, REDIS_CONFIG
from CrawlPage.utils import MongoDB
from CrawlPage.RedisClient import RedisClient

if __name__ == '__main__':
    # 加载.env配置文件
    load_dotenv()
    # 初始化redis
    REDIS_DB = int(os.getenv('REDIS_DB', 4))
    CLS_PATTERN = os.getenv('CLS_PATTERN', 'A.{4,}')
    REDIS_CONFIG['db'] = REDIS_DB
    redis = RedisClient(**REDIS_CONFIG)
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