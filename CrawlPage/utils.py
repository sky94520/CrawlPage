import pymongo
import requests
from datetime import datetime, timedelta


def str2date(date_string):
    if date_string is None or len(date_string) == 0:
        return None
    date = datetime.strptime(date_string, '%Y-%m-%d')
    return date


def date2str(date):
    date_string = date.strftime('%Y-%m-%d')
    return date_string


class MongoDB(object):

    def __init__(self, host, port):
        self.mongo = pymongo.MongoClient(host=host, port=port)

    def authenticate(self, db_name, name, password):
        db = self.mongo[db_name]
        db.authenticate(name=name, password=password)

    def get_db(self, name):
        return self.mongo[name]


if __name__ == '__main__':
    from CrawlPage.config import MONGO_CONFIG
    mongo = MongoDB(host=MONGO_CONFIG['ip'], port=MONGO_CONFIG['port'])
    mongo.authenticate(db_name=MONGO_CONFIG['database'], name=MONGO_CONFIG['username'], password=MONGO_CONFIG['password'])

    db = mongo.get_db('patent')
    collection = db['ipc_category']

    results = collection.find({'code': {'$regex': '.{4,}'}})
    for result in results:
        print(result)

    queue = ['A']
    index = 0

    # while len(queue) > 0:
    #     code = queue[0]
    #     queue.pop(0)

    #     result = collection.find_one({'code': code})
    #     if len(code) > 4:
    #         print('code:%s, name:%s' % (code, result['title']))

    #     if 'children' in result:
    #         for child in result['children']:
    #             queue.append(child['code'])
