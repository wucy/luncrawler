#! /usr/bin/env python3


import os
import sys
import re
import concurrent.futures
import io
from html.parser import HTMLParser
from urllib.request import urlopen
from bs4 import BeautifulSoup
import chardet


WEB_TIME_OUT = 5 #sec
WEB_RETRY_TIMES = 4

def run_array_jobs(num_worker, func, job_array, root):
    csv_info = open(csv_info_fn, 'w')
    csv_info.write('id,longitude,latitude,heading\n')

    csv_score = open(csv_score_fn, 'w')
    csv_score.write('id,score\n')

    cnt = 1
    ret = list()
    executor = concurrent.futures.ProcessPoolExecutor(max_workers=num_worker)
    fut_lst = list()
    for args in job_array:
        if isinstance(args, (list, tuple)):
            future = executor.submit(func, *args)
        else:
            future = executor.submit(func, args)
        fut_lst.append(future)
        

    res = None
    for future in fut_lst:
        try:
            res = future.result(timeout=30)
        except Exception as e:
            print(e)
            res = None
        if res == None:
            continue
        new_fn = 'data/pics/' + str(cnt) + '.jpg'
        raw_fn = res[0]
        #print(raw_fn)
        if os.path.exists(new_fn):
            os.remove(new_fn)
        longitude = res[1]
        latitude = res[2]
        heading = res[3]
        os.rename(raw_fn, new_fn)
        csv_info.write(str(cnt) + ',' + str(longitude) + ',' + str(latitude) + ',' + heading + '\n')
        csv_score.write(str(cnt) + ',\n')

        cnt += 1
        #if cnt > 3320:
        #    break

    csv_info.close()
    csv_score.close()

def clean_content(content):
    content = fetch_content('http://news.sina.com.cn/c/nd/2016-01-18/doc-ifxnqrkc6603044.shtml')[1]
    charset = chardet.detect(content)
    ret = content.decode(charset['encoding'], 'replace')
    ret = BeautifulSoup(ret, 'html.parser', from_encoding=charset).get_text()
    return ret
def fetch_content(addr):
    for i in range(WEB_RETRY_TIMES):
        good = True
        content = None
        codec = None
        try:
            content = urlopen(addr, None, WEB_TIME_OUT).read()
        except:
            print('[Timeout] Retry=%d, Addr=%s' % (i, addr))
            good = False
        if not good:
            continue
        else:
            return (addr, content)
    print('[Failed] Addr=%s' % (addr))
def one_baidunews_job():
    pass
def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf8')
    
    print(clean_content(None))
    
if __name__ == '__main__':
    main()
