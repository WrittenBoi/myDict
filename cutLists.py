#!/usr/bin/env python3

import os
import sys
import pickle
import shutil
from pydub import AudioSegment as ASEG

DICT_DB = r"scratched/dictDB_1-1597.pkl"
SND_IDX_DB = r"scratched/sndIdxUS.pkl"
#SND_IDX_DB = r"scratched/sndIdxUK.pkl"
ORG_SND_BASE = r"scratched/pronunciation/US"
#ORG_SND_BASE = r"scratched/pronunciation/UK"
WORD_LIST_RAW = r"list.txt"

OUTPUT_PATH = r"scratched/splitted"
OUTPUT_TXT_FMT = "%04d-%04d.txt"
OUTPUT_SND_FMT = "%04d-%04d.mp3"

BULK_NUM = 60


def showAWord(fout, word, seq, explanation):
    ct,yb,lj = explanation
    indent = "  "
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

def gen_txt_file(wordLst, wordDict, st, ed):
    output_fname = os.path.join(OUTPUT_PATH, OUTPUT_TXT_FMT % (st, ed))
    with open(output_fname, "w+") as f:
        for idx in range(st, ed+1):
            try:
                word = wordLst[idx]
                explan = wordDict[word]
                showAWord(f, word, idx, explan)
            except(KeyError):
                print("Warning: No explan of %04d(%s)" % (idx, wordLst[idx]))
                continue


def gen_snd_file(wordLst, sndIdx, st, ed, interval=1):
    ret_audio = ASEG.empty()
    blank = ASEG.silent(duration=interval*1000)
    output_fname = os.path.join(OUTPUT_PATH, OUTPUT_SND_FMT % (st, ed))

    for idx in range(st, ed+1):
        try:
            #snd_name = sndIdx[idx]
            snd_name = sndIdx[wordLst[idx]]
            #org_snd_path = os.path.join(ORG_SND_BASE, snd_name)
            #ret_audio += ASEG.from_file(org_snd_path, format="mp3") + blank
            ret_audio += ASEG.from_file(snd_name, format="mp3") + blank
        except(KeyError):
            print("Warning: No sound of %04d(%s)" % (idx, wordLst[idx]))
            continue

    ret_audio.export(output_fname, format="mp3")

def load_all_db(*dbLst):
    ret = []
    for e in dbLst:
        with open(e, "rb") as f:
            ret.append(pickle.load(f))

    return tuple(ret)

def getWordList(fpath):
    wordLst = []
    with open(fpath, "r") as f:
        return [ e.strip("\r\n") for e in f if len(e) != 0 and e[0] != '@' ]

if __name__ == '__main__':
    if os.path.exists(OUTPUT_PATH):
        shutil.rmtree(OUTPUT_PATH)

    os.makedirs(OUTPUT_PATH)

    wordLst = getWordList(WORD_LIST_RAW)
    wordNum = len(wordLst)
    wordLst.insert(0, None)

    wordDict, sndIdx = load_all_db(DICT_DB, SND_IDX_DB)

    for idx in range(1, wordNum, BULK_NUM):
        st = idx
        ed = idx + BULK_NUM - 1
        if(ed > wordNum):
            ed = wordNum
        gen_snd_file(wordLst, sndIdx, st, ed)
        gen_txt_file(wordLst, wordDict, st, ed)
