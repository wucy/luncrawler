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
import socket


WEB_TIME_OUT = 1 #sec
WEB_RETRY_TIMES = 4

socket.setdefaulttimeout(WEB_TIME_OUT)

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
            res = future.result(timeout=5)
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
        response = None
        try:
            response = urlopen(addr, None, WEB_TIME_OUT)
            content = response.read()
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
    return (addr, ''.encode('utf-8'))

bd_onepage_pat = re.compile('<h3 class="c\-title"><a href=[\'"]?([^\'" >]+)')
def get_baidu_onepage_lst(lnk):
    raw = fetch_content(lnk)[1].decode('utf-8')
    ret = bd_onepage_pat.findall(raw)
    return ret
def baidunews_job_lst():
    rn = 50
    pn = 0
    lst = list()
    while pn < 8500:
        lnk = 'http://news.baidu.com/ns?word=%E5%8C%97%E4%BA%AC%E6%97%A7%E5%9F%8E&pn=' + str(pn) + '&cl=2&ct=1&tn=news&rn=' + str(rn) + '&ie=utf-8&bt=0&et=0&rsv_page=-1'
        lst.extend(get_baidu_onepage_lst(lnk))
        pn += rn
    return lst
def main_baidu(refresh=True):
    os.system('mkdir -p baidu/raw')
    os.system('mkdir -p baidu/archive')
    job_lst = None
    if refresh:
        job_lst = baidunews_job_lst()
        lstf = open('baidu/news.lst', 'w')
        lstf.write(str(job_lst))
        lstf.close()
    else:
        job_lst = eval(open('baidu/news.lst', 'r').readline())
    print (len(job_lst))
    run_array_jobs(20, one_baidu_job, job_lst)
def one_baidu_job(lnk):
    raw = fetch_content(lnk)
    name =  hashlib.md5(lnk.encode('utf-8')).hexdigest()
    fn = 'baidu/raw/' + name
    f = open(fn, 'w')
    f.write(raw[1].decode('utf-8'))
    f.close()
    #archive = clean_content(raw[1])
    #fn = 'baidu/archive/' + name
    #f = open(fn, 'w')
    #f.write(archive)
    #f.close()

def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
    #get_baidu_onepage_lst('http://news.baidu.com/ns?word=%E5%8C%97%E4%BA%AC%E6%97%A7%E5%9F%8E&pn=40&cl=2&ct=1&tn=news&rn=20&ie=utf-8&bt=0&et=0&rsv_page=1')
    main_baidu(refresh=False)
if __name__ == '__main__':
    main()
