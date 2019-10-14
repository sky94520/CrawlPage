# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import re
import os
import json


class JsonPipeline(object):

    def process_item(self, item, spider):
        basedir = spider.settings.get('BASEDIR')
        main_cls_number = re.sub('/', '-', spider.main_cls_number)
        path = os.path.join(basedir, 'files', 'page_links', main_cls_number)
        response = item['response']
        index = response.meta['index']

        if not os.path.exists(path):
            os.makedirs(path)

        filename = os.path.join(path, '%s.json' % index)
        with open(filename, "w", encoding='utf-8') as fp:
            fp.write(json.dumps(item['array'], ensure_ascii=False, indent=2))
        return item


class SavePagePipeline(object):

    def process_item(self, item, spider):
        # 文件存储路径
        basedir = spider.settings.get('BASEDIR')
        main_cls_number = re.sub('/', '-', spider.main_cls_number)
        path = os.path.join(basedir, 'files', 'page', main_cls_number)
        response = item['response']
        index = response.meta['index']

        if not os.path.exists(path):
            os.makedirs(path)
        filename = os.path.join(path, '%s.html' % index)
        with open(filename, "wb") as fp:
            fp.write(response.body)
        return
