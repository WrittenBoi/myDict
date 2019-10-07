#!/usr/bin/env python3
import os
import sys
import re
import requests
import pickle
from lxml import etree
from time import sleep

baseURL = "http://cn.bing.com/dict/search?q="
SND_DEST = "mp3"
REQ_TIMEOUT = 10
WORD_LIST_RAW = r"list.txt"
OUT_BASE_DIR = r"scratched"
DICT_FILE = r"dictScratched.txt"
SND_BASE_PATH = r"pronunciation"
SLEEP_INTV = 0.1
CONV_DICT = {"美":"US", "英":"UK"}
SND_SAVE_CONTRY = CONV_DICT["美"]
SND_IDX_DUMP = "%s/sndIdx%s.pkl" % (OUT_BASE_DIR, SND_SAVE_CONTRY)
RETRY = 5
RETRY_INTV = 5

"""
response  = requests.get("https://www.baidu.com")
print(type(response))
print(response.status_code)
print(type(response.text))
print(response.text)
print(response.cookies)
print(response.content)
print(response.content.decode("utf-8"))
"""

def saveDataBase(stSeq, edSeq, obj):
    fName = "dictDB_%d-%d.pkl" % (stSeq, edSeq)
    filePath = os.path.join(OUT_BASE_DIR, fName)
    with open(filePath, "wb+") as f:
        pickle.dump(obj, f)

def saveContext(text):
    with open("html.txt", "w+") as f:
        f.write(text)

def getSnd(outName, url):
    resp = requests.get(url, timeout=REQ_TIMEOUT)
    if(resp.status_code == 200):
        with open(outName, "bw+") as f:
            f.write(resp.content)
        #print("Saved: ", outName)
        return True
    else:
        print("Get sound NG: ", outName)
        return False

def saveOneSnd(word, idx, country, url, bashPath, sndFileDict):
    outPath = os.path.join(bashPath, country)
    if not os.path.exists(outPath):
        os.makedirs(outPath)
    sndName = "%04d_%s.%s" % (idx, word, url.split('.')[-1])
    outPath = os.path.join(outPath, sndName)

    for retry in range(RETRY):
        try:
            if(getSnd(outPath, url)):
                if(country == SND_SAVE_CONTRY):
                    sndFileDict[word] = outPath
                return
        except Exception as ERR:
            if(retry == 0):
                print()
            print(retry, ERR)
            sleep(RETRY_INTV)

def getOnePage(word):
    postWD = word.replace(" ", "%20")
    postWD = postWD.replace("'", "%27")

    resp = requests.get(baseURL + postWD)
    if(resp.status_code == 200):
        text = resp.content.decode("utf-8")
        #print("Got: ", word)
        #saveContext(text)
        return text
    else:
        print("error!")
        return None

#获得单词释义
def get_citiao(html_selector):
    citiao=[]
    hanyi_xpath='/html/body/div[1]/div/div/div[1]/div[1]/ul/li'
    get_hanyi=html_selector.xpath(hanyi_xpath)
    for item in get_hanyi:
        it=item.xpath('span')
        citiao.append('[%s] %s'%(it[0].text,it[1].xpath('span')[0].text))

    return citiao

#获得单词音标和读音连接
def get_yinbiao(html_selector):
    yinbiao=[]
    yinbiao_xpath='/html/body/div[1]/div/div/div[1]/div[1]/div[1]/div[2]/div'
    bbb="(https\:.*?mp3)"
    reobj1=re.compile(bbb,re.I|re.M|re.S)
    get_yinbiao=html_selector.xpath(yinbiao_xpath)
    for item in get_yinbiao:
        it=item.xpath('div')
        if len(it)>0:
            ddd=reobj1.findall(it[1].xpath('a')[0].get('onmouseover',None))
            org,yb = it[0].text.split('\xa0')
            yinbiao.append((org, yb, ddd[0]))
            ddd=reobj1.findall(it[3].xpath('a')[0].get('onmouseover',None))
            org,yb = it[2].text.split('\xa0')
            yinbiao.append((org, yb, ddd[0]))

    return yinbiao

#获得例句
def get_liju(html_selector):
    liju=[]
    get_liju_e=html_selector.xpath('//*[@class="val_ex"]')
    get_liju_cn=html_selector.xpath('//*[@class="bil_ex"]')
    get_len=len(get_liju_e)
    for i in range(get_len):
        liju.append("%s %s"%(get_liju_e[i].text,get_liju_cn[i].text))

    return liju

def getOneWord(word):
    for retry in range(RETRY):
        try:
            pageHtml = getOnePage(word)
            if(pageHtml != None):
                selector = etree.HTML(pageHtml)
                # 获取词条
                ciTiao = get_citiao(selector)
                # 获取音标
                yinBiao = get_yinbiao(selector)
                # 获取例句
                liJu = get_liju(selector)
                return (ciTiao, yinBiao, liJu)
            else:
                return None
        except Exception as ERR:
            if(retry == 0):
                print()
            print(retry, ERR)
            sleep(RETRY_INTV)
    return None

def showAWord(fout, word, seq, explanation, sndFileDict):
    ct,yb,lj = explanation
    indent = "  "
    basePath = os.path.join(OUT_BASE_DIR, SND_BASE_PATH)
    # 显示单词
    #print("%d %s  " % (seq, word), file=fout, end='')
    print("%d %s" % (seq, word), file=fout)
    # 显示音标
    ybExist = False
    for e in yb:
        # 输出音标
        if(len(e[1]) > 0):
            print(indent, end='', file=fout)
            print("%s%s" % (e[0], e[1].strip()), end='', file=fout)
            ybExist = True
        # 保存读音
        if(len(e[2]) > 0):
            saveOneSnd(word, seq, CONV_DICT[e[0]], e[2], basePath, sndFileDict)
        else:
            print("No sound for:", word, e[0])
    if(ybExist):
        print(file=fout)
    # 显示释意
    if(len(ct) > 0):
        for e in ct:
            print("%s%s" % (indent, e), file=fout)
    # 显示例句
    if(len(lj) > 0):
        for e in lj:
            print("%s%s" % (indent, e), file=fout)
            break
    print(file=fout)


def getWordList(fpath):
    wordLst = []
    with open(fpath, "r") as f:
        return [ e.strip("\r\n") for e in f if len(e) != 0 and e[0] != '@' ]


#wordLst = getWordList(WORD_LIST_RAW)
#for idx in range(len(wordLst)):
#    print(idx, wordLst[idx])
#
#exit(0)

if __name__ == '__main__':
    if not os.path.exists(OUT_BASE_DIR):
        os.makedirs(OUT_BASE_DIR)

    sndFileDict = {}
    wordDict = {}
    result_file = os.path.join(OUT_BASE_DIR, DICT_FILE)
    with open(result_file, "w+") as fout:
        wordLst = getWordList(WORD_LIST_RAW)
        wordLst.insert(0, None)
        #for idx in range(1, len(wordLst), 500):
        for idx in range(1, len(wordLst)):
            print(idx, wordLst[idx], "%d%%" % (idx/len(wordLst)*100), end=' ')
            explan = getOneWord(wordLst[idx])
            if(explan == None):
                print("NG")
                sleep(SLEEP_INTV)
                continue
            wordDict[wordLst[idx]] = explan
            showAWord(fout, wordLst[idx], idx, explan, sndFileDict)
            print("OK")
            sleep(SLEEP_INTV)

    saveDataBase(1, len(wordLst)-1, wordDict)
    with open(SND_IDX_DUMP, "wb+") as f:
        pickle.dump(sndFileDict, f)

