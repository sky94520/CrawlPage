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
    pass
