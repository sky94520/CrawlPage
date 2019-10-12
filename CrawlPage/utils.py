import pymongo
import requests
from datetime import datetime, timedelta


def get_cookie(code="*", proxies=None, **kwargs):
    """
    根据条件给知网发送post请求来获取对应的cookie
    :param code: 条件，知网会根据条件来进行搜索
    :param proxies: 代理 proxies = {'http': 'host:port', 'https': 'host:port'}
    :return: cookie 字符串类型，主要用于赋值到header中的Cookie键
    headers = {'Cookie': cookie}
    """
    params = {
        "action": "",
        "NaviCode": code,
        "ua": "1.25",
        "isinEn": "0",
        "PageName": "ASP.brief_result_aspx",
        "DbPrefix": "SCPD",
        "DbCatalog": "中国专利数据库",
        "ConfigFile": "SCPD.xml",
        "db_opt": "SCOD",
        "db_value": "中国专利数据库",
        "his": "0",
        "__": _get_now_gmt_time()
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


def _get_now_gmt_time():
    """
    获取当前的中国标准时间，主要用于赋值给form data
    :return: 当前的时间字符串
    """
    GMT_FORMAT = '%a %b %d %Y %H:%M:%S GMT+0800'
    now = datetime.utcnow() + timedelta(hours=8)
    text = '%s (中国标准时间)' % now.strftime(GMT_FORMAT)
    return text


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
