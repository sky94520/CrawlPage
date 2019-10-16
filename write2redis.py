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
    REDIS_DB = int(os.getenv('REDIS_DB', 5))
    CLS_PATTERN = os.getenv('CLS_PATTERN', 'A.{4,}')
    REDIS_CONFIG['db'] = REDIS_DB
    redis = RedisClient(**REDIS_CONFIG)
    # 初始化mongo
    mongo = MongoDB(host=MONGO_CONFIG['ip'], port=MONGO_CONFIG['port'])
    mongo.authenticate(db_name=MONGO_CONFIG['database'], name=MONGO_CONFIG['username'],
                       password=MONGO_CONFIG['password'])

    db = mongo.get_db('patent')
    collection = db['ipc_category']
    queue = [chr(ord('A') + i) for i in range(8)]
    buffers = []
    while len(queue) > 0:
        cls_code = queue[0]
        queue.pop(0)

        result = collection.find_one({'code': cls_code})
        if 'children' in result:
            for child in result['children']:
                if len(child['code']) < 4:
                    queue.append(child['code'])
                elif len(child['code']) == 4:
                    buffers.append(child['code'])
    print(buffers)
    # 写入
    redis.redis.rpush('queue', *buffers)
    print('写入成功%d' % len(buffers))
