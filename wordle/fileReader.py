#Author: Hayk Aleksanyan

import re
import codecs
import chardet #for determining the encoding of files

from pathlib import Path

from os import getcwd
from os import listdir
from os.path import isfile, join



def readFrom(fName):
    """
      tries to determine the correct encoding of the file and read its content
      returns the list of lines of the file with empty lines dropped
    """

    content = []
    encoding_name = ''

    try:
        with open(fName, 'rb') as f:
            f1 = bytearray(f.read())
            encoding_name = chardet.detect(f1)['encoding']
    except:
        encoding_name = 'utf-8' #the default try


    try:
        with codecs.open(fName, encoding = encoding_name) as f:
            content = f.readlines()
    except:
        content = []


    return  [x.strip() for x in content if len(x.strip()) > 0]

def wrapinto_string(content_in_Lines):
    """
     gets a list of lines read from a file
     returns a single string, where all lines are merged
     with special white-space chars are removed and extra spaces trimmed into 1.
    """

    res = " ".join(content_in_Lines)

    #remove certain special characters from the string
    for c in {'\a', '\b', '\f', '\n', '\r', '\t'}:
        res = res.replace(c, ' ')

    r1 = re.compile(' {2,}')      #strips off the extra white-spaces
    res = re.sub(r1, ' ', res)

    return res.strip()


def tokenize_file_IntoWords(fName, printStepInfo = True):
    """
      read and pre-process a given a text file
      and return a LIST of raw tokens (no groupping or case-folding of tokens)

      if printStepInfo == True, then we print small messages for the steps of this procedure,
      otherwise, the process runs silently.
    """

    content = readFrom(fName)
    if printStepInfo == True:
        print('number of rows in the original file is ' + str(len(content)) )

    if len(content) == 0:
        if printStepInfo == True:
            print('No content: tokenization is terminated.' )
        return []


    strData = wrapinto_string(content)
    if printStepInfo == True:
        print('length of the wrapped string is ' + str(len(strData)) )


    r1 = re.compile(r'[^\w -]') #remove all non-alphanumeric, non-space, non-hyperhen chars (unicode - supported)
    strData = re.sub(r1, ' ', strData)

    r1 = re.compile(' {2,}') #strips off the extra whitespaces
    strData = re.sub(r1, ' ', strData)

    strData = strData.strip()

    res = []   # the final list of Tokens to be returned.
    X = strData.split(' ')
    for w in X:
        if len(w) > 2:
            res.append(w.strip('-'))

    if printStepInfo == True:
        print('the number of tokens equals ' + str(len(res)) )

    return res

def tokenGroup(tokens, removeStopWords = True):
    """
      gets a list of raw tokens (strings) and returns 2 lists
      where the 1st is the grouped (unique) list of the original tokens, and the 2nd is their frequency
      returns the sorted (according to decreasing frequencies) lists
    """

    group = dict()
    for t in tokens:
        if removeStopWords == True and t.lower() in stop_words:
            continue

        if not t in group:
            group[t] = 1
        else:
            group[t] += 1

    # we now sort the tokens according to decreasing frequencies
    if len(group) == 0:
        return {}

    tokenSorted, tokenFreq = [], []
    for (word, freq) in sorted(group.items(), key = lambda p: -p[1]):
        tokenSorted.append(word)
        tokenFreq.append(freq)

    return tokenSorted, tokenFreq



#  - - - - - globals - - - - -

stop_words = readFrom('stop-words.txt')  # List of predefined stop-words.
                                         # NOTE!! in final module, this should go to the end, since needs readFrom function.
#print('number of stop words is ' + str(len(stop_words) ) )
