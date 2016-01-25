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
from boilerpipe.extract import Extractor
import hashlib
import json
import time

WEB_TIME_OUT = 5 #sec
WEB_RETRY_TIMES = 4

def run_array_jobs(num_worker, func, job_array):
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
            res = future.result(timeout=10)
        except Exception as e:
            print(e)
            res = None
        if res == None:
            continue

def clean_content(content):
    extractor = Extractor(extractor = 'ArticleExtractor', html = content)
    return extractor.getText()
def fetch_content(addr):
    for i in range(WEB_RETRY_TIMES):
        good = True
        content = None
        codec = None
        try:
            content = urlopen(addr, None, WEB_TIME_OUT).read()
            charset = chardet.detect(content)
            text = content.decode(charset['encoding'], 'replace').encode('utf-8')
        except:
            print('[Timeout] Retry=%d, Addr=%s' % (i, addr))
            good = False
        if not good:
            continue
        else:
            return (addr, text)
    print('[Failed] Addr=%s' % (addr))
    return (addr, '')

pattern = re.compile('\'url\': \'([^\']+)\'')
def get_blog163_onepage_lst(lnk):
    raw = fetch_content(lnk)[1].decode('utf-8')
    json_lst_raw = json.loads(raw)
    ret = pattern.findall(str(json_lst_raw))
    time.sleep(0.1)
    print(raw)
    return ret
search_token = '%E5%8C%97%E4%BA%AC%E6%97%A7%E5%9F%8E+site%3Ablog.sina.com.cn'
key = 'AIzaSyCxt38BIEkOpgPsa9emCzCvj5BWoLif7BY'
search_marco = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&q=%s&rsz=large&start=%d&key=%s'
def blog163news_job_lst():
    sta = 0
    lst = list()
    cnt = 0
    while sta < 8000 and cnt < 800:
        lnk = search_marco % (search_token, sta, key)
        sub_lst = get_blog163_onepage_lst(lnk)
        lst.extend(get_blog163_onepage_lst(lnk))
        sta += len(sub_lst)
        cnt += 1
        print('tot=%d,cnt=%d' % (sta, cnt))
        if len(sub_lst) == 0:
            break
    return lst
def main_blog163(refresh=True):
    os.system('mkdir -p blog163/raw')
    os.system('mkdir -p blog163/archive')
    job_lst = None
    if refresh:
        job_lst = blog163news_job_lst()
        lstf = open('blog163/news.lst', 'w')
        lstf.write(str(job_lst))
        lstf.close()
    else:
        job_lst = eval(open('blog163/news.lst', 'r').readline())
    print(len(job_lst))
    #run_array_jobs(20, one_blog163_job, job_lst)
def one_blog163_job(lnk):
    raw = fetch_content(lnk)
    name =  hashlib.md5(lnk.encode('utf-8')).hexdigest()
    fn = 'blog163/raw/' + name
    f = open(fn, 'w')
    f.write(raw[1].decode('utf-8'))
    f.close()
    archive = clean_content(raw[1])
    fn = 'blog163/archive/' + name
    f = open(fn, 'w')
    f.write(archive)
    f.close()

def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
    #get_blog163_onepage_lst('http://news.blog163.com/ns?word=%E5%8C%97%E4%BA%AC%E6%97%A7%E5%9F%8E&pn=40&cl=2&ct=1&tn=news&rn=20&ie=utf-8&bt=0&et=0&rsv_page=1')
    main_blog163(refresh=True)
if __name__ == '__main__':
    main()
