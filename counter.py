import os
import re
import csv
import pprint
import json
import operator
from collections import Counter
import pprint


basedir = os.path.realpath(os.path.dirname(__file__))
work_path = os.path.join(basedir, 'files')
detail_path = os.path.join(work_path, 'page_links')
save_path = os.path.join(work_path, 'csv')


def count_patents(company, ipc, topK=3):
    """
    遍历page_links文件夹，并进行统计
    :param company: 公司名称
    :param ipc: ipc类目
    :param topK: 获取前若干个公司的名称和对应的个数
    :return:
    """
    # 遍历
    real_pathname = re.sub('/', '-', ipc)
    path = os.path.join(detail_path, real_pathname)
    if not os.path.exists(path):
        return
    total_count = 0
    counter = Counter()
    for parent, dirnames, filenames in os.walk(path, followlinks=False):
        cls_number = os.path.split(parent)[-1]
        for filename in filenames:
            fullpath = os.path.join(parent, filename)
            fp = open(fullpath, 'r', encoding='utf-8')
            data = json.load(fp)
            fp.close()
            # 统计数据
            total_count += len(data)
            # 遍历数据
            for datum in data:
                publication_number = datum['filename']
                applicants = datum['applicants'].split(';')
                for applicant in applicants:
                    if '大学' in applicant or '学院' in applicant:
                        continue
                    counter[applicant] = counter[applicant] + 1
        print('%s:%d' % (cls_number, total_count))
        if total_count == 0:
            continue
    # 排序
    sortedCounter = sorted(counter.items(), key=operator.itemgetter(1), reverse=True)
    # pprint.pprint(sortedCounter)
    path = os.path.join(save_path, '%s.csv' % real_pathname)
    with open(path, 'w', encoding='utf-8') as fp:
        for datum in sortedCounter:
            fp.write('%s,%s\n' % (datum[0], datum[1]))
    result = {'top': sortedCounter[:topK], 'count': total_count}
    for (name, number) in sortedCounter:
        if company == name:
            result['top'].append((name, number))
    # 返回数据
    return result


if __name__ == '__main__':
    # 获取各个公司的代表IPC
    fp = open(os.path.join(work_path, 'result.csv'), 'r', encoding='utf-8')
    reader = csv.reader(fp)
    for (company, ipc) in reader:
        result = count_patents(company, ipc)
        if not result:
            continue
        print(company, ipc)
        print(result)
    fp.close()
    # count_patents()
