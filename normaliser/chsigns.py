#!/usr/bin/env python
# -*- coding: utf-8 -*-

# (C) 2006, 2008, 2010, 2012-2014 Dublin City University
# All rights reserved. This material may not be
# reproduced, displayed, modified or distributed without the express prior written
# permission of the copyright holder.

# Author: Joachim Wagner

import array
import base64
import gzip
import math
import sha
import random
import re
import string
import sys
import time


opt_more_currencies = False    # support SFr, DM etc not just $, US$ etc
opt_require_amount  = True     # edit DM5,000/NN0 but not DM/NN0 5,000/CRD
opt_separate_dashes = True     # separate sequences of two or more dashes (--[-]*)

signs = {
    u'\N{pound sign}'.encode('utf-8'):  '$',   # whitespace is added after $
    u'\N{yen sign}'.encode('utf-8'):    '$',
    u'\N{en dash}'.encode('utf-8'):     '-',   # 1970-75 PTB style
    u'\N{em dash}'.encode('utf-8'):     '--',  # PTB style, '---' not in PTB
    u'\N{soft hyphen}'.encode('utf-8'): '',    # note effects of option --freq
    u'\N{horizontal ellipsis}'.encode('utf-8'):            '...',
    u'\N{vulgar fraction one quarter}'.encode('utf-8'):    '1/4',
    u'\N{vulgar fraction one half}'.encode('utf-8'):       '1/2',
    u'\N{vulgar fraction three quarters}'.encode('utf-8'): '3/4',
    # other fractions (U+2153 to 215E) are very rare in the BNC
    u'\N{double prime}'.encode('utf-8'):        '"',
    u'\N{prime}'.encode('utf-8'):               '\'',
    u'\N{left single quotation mark}'.encode('utf-8'):     '\'', # '``' or '\'' depending on corpus
    u'\N{right single quotation mark}'.encode('utf-8'):    '\'',
    u'\N{left-pointing double angle quotation mark}'.encode('utf-8'):     '``',
    u'\N{right-pointing double angle quotation mark}'.encode('utf-8'):    '\'\'',
    #u'\N{bullet}'.encode('utf-8'):              '*',    # not in PTB
    u'\N{multiplication sign}'.encode('utf-8'): 'x',
    #u'\N{micro sign}'.encode('utf-8'):          '\xb5', # not in PTB
    '............': '...',
    '...........': '...',
    '..........': '...',
    '.........': '...',
    '........': '...',
    '.......': '...',
    '......': '...',
    '.....': '...',
    '....': '...',
    ',,,,,,,,': ',',
    ',,,,,,,': ',',
    ',,,,,,': ',',
    ',,,,,': ',',
    ',,,,': ',',
    ',,,': ',',
    ',,': ',',
    '!!!!!!!': '!',
    '!!!!!!': '!',
    '!!!!!': '!',
    '!!!!': '!',
    '!!!': '!',
    '!!': '!',
    '???????': '?',
    '??????': '?',
    '?????': '?',
    '????': '?',
    '???': '?',
    '??': '?',
}

if opt_more_currencies:
    signs[u'\N{euro sign}'.encode('utf-8')] = '$'

signs_max_key_len = 0
for key in signs.keys():
    if len(key) > signs_max_key_len:
        signs_max_key_len = len(key)

# TODO: be much more restrictive here, especially if to be used
#       without opt_require_amount
moreCurrencies = '|([A-Z][A-Za-z]{1,2})'

currency  = '([A-Z]{,3}[$])'
if opt_more_currencies and not opt_require_amount:
    currency = currency + moreCurrencies

amount    = '([0-9,.]+)|(hundred)|(thousand)|(million)|(billion)|(trillion)'
anyTag    = '/[A-Z0-9-]+ '

reTaggedCurrency = re.compile(' (?P<CURRENCY>' + currency + ')' + anyTag)

if opt_more_currencies and opt_require_amount:
    currency = currency + moreCurrencies

reTaggedCurrencyAndAmount = re.compile(
    ' (?P<CURRENCY>' + currency + ')(?P<AMOUNT>' + amount + ')' + anyTag
)

reTaggedCurrencyEquation = re.compile(
    ' (?P<CURRENCY1>' + currency + ')(?P<AMOUNT1>(' + amount + ')?)'
    '=(?P<CURRENCY2>(' + currency + ')?)(?P<AMOUNT2>' + amount + ')' + anyTag
)

reDashes = re.compile('--[-]*')

hash2logfreq = {}

def token2hash(token):
    m = sha.new(token)
    return m.digest()[:8]
    
def readfreq(filename, verbose = True):
    global token2logfreq
    if verbose:
        sys.stderr.write('building frquency table\n')
    sys.stderr.write('\treading frequencies\n')
    fin = open(filename, 'rb')
    while 1:
        line = fin.readline()
        if not line:
            break
        elements = line.split()
        count = float(elements[0])
        token = string.join(elements[1:])
        index = token2hash(token)
        logfreq = int(16777216.0 * math.log(count))
        if hash2logfreq.has_key(index):
            mmindex = string.rstrip(base64.encodestring(index))
            sys.stderr.write('\tcollision at %s for %s\n' %(mmindex, token))
            logfreq = int((hash2logfreq[index] + logfreq) / 2)
        hash2logfreq[index] = logfreq
    sys.stderr.write('\t%s\n' %time.ctime(time.time()))
    fin.close()

def getLogFreq(token):
    global token2logfreq
    index = token2hash(token)
    try:
        return hash2logfreq[index]
    except KeyError:
        return 0

def disambiguateSoftHyphens(sentence, withBigrams = False):
    newTokens = []
    softhyphen = u'\N{soft hyphen}'.encode('utf-8')
    for token in sentence.split():
        index = token.find(softhyphen)
        if index >= 0:
	    token1 = token.replace(softhyphen, '-')
            token2 = token.replace(softhyphen, ' ')
            token3 = token.replace(softhyphen, '')
            if withBigrams:
                negLogFreq2 = -getLogFreq(token2)
            else:
                negLogFreq2 = 0.0
            freqAndToken = [
                (-getLogFreq(token1), 1, token1),
                (negLogFreq2,         2, token2),
                (-getLogFreq(token3), 3, token3),
            ]
            freqAndToken.sort()
            token = freqAndToken[0][2]
        newTokens.append(token)
    return string.join(newTokens)

def usage():
    sys.stderr.write("Usage:")
    sys.stderr.write(' %s [options] [*.cinput|*.sgml[.gz|.bz2]]\n' %sys.argv[0])
    sys.stderr.write('Options:\n')
    sys.stderr.write('\t--header      output <file name="..."> for each file\n')
    sys.stderr.write('\t--verbose     output progress info\n')
    #sys.stderr.write('\t--quiet       do not output progress info (default)\n')
    sys.stderr.write('\t--freq <f>    file with token counts for soft hyphen disambiguation\n')
    sys.stderr.write('\t--bigrams     frequency file also contains bigrams\n')
    sys.stderr.write('\t--tagged      support BNC POS tags (currently not supported with --bigrams)\n')
    sys.stderr.write('\t--raw         read and write plain text (default: sgml)\n')
    sys.stderr.write('\t--help        print this message\n')


def main():
    global signs
    opt_header  = False
    opt_verbose = False
    opt_freq    = None
    opt_bigrams = False
    opt_raw     = False
    opt_tagged  = False
    while len(sys.argv) > 1 and sys.argv[1][:2] == '--':
        arglen = 1
        if sys.argv[1] == '--':
            del sys.argv[1]
            break
        elif sys.argv[1] == '--header':
            opt_header         = True
        elif sys.argv[1] == '--tagged':
            opt_tagged         = True
        elif sys.argv[1] == '--raw':
            opt_raw            = True
        elif sys.argv[1] == '--bigrams':
            opt_bigrams        = True
        elif sys.argv[1] == '--verbose':
            opt_verbose        = True
        elif sys.argv[1] == '--quiet':
            # obsolete
            opt_verbose        = False
        elif sys.argv[1] == '--freq':
            opt_freq = sys.argv[2]
            arglen = 2
        elif sys.argv[1] == '--help':
            usage()
            sys.exit(0)
        else:
            sys.stderr.write('unknown option %s\n' %`sys.argv[1]`)
            sys.exit(1)
        for i in range(arglen):
            del sys.argv[1]
    if opt_bigrams and opt_tagged:
        raise NotImplementedError, 'cannot use --tagged and --bigrams together'
    if opt_freq:
        readfreq(opt_freq, opt_verbose)
    if len(sys.argv) < 2:
        # no file provided on command line
        # -> add None to the file list to mark reading from stdin
        sys.argv.append(None)
    lastStat = 0.0
    softhyphen = u'\N{soft hyphen}'.encode('utf-8')
    for filename in sys.argv[1:]:
        if filename is None:
            infile = sys.stdin
        elif filename[-3:] == '.gz':
            infile = gzip.GzipFile(filename, 'rb')
        else:
            infile = open(filename, 'rb')
        if opt_header:
            sys.stdout.write('<file %s>\n' %filename)
        lineNo = 0
        while 1:
            line = infile.readline()
            if not line:
                break
            if opt_verbose:
                lineNo = lineNo + 1
                now = time.time()
                if now > lastStat + 0.5:
                    sys.stderr.write('%s line %s \r' %(filename, lineNo))
                    lastStat = now
            if opt_raw:
                sentence = line.rstrip()
                prefix = ''
                suffix = '\n'
            else:
                start = line.find('>')
                end   = line.rfind('<')
                if start < 0 or end < 0:
                    raise ValueError, 'input line is missing tags'
                sentence =  line[start+1:end]
                prefix = line[:start+1]
                suffix = line[end:]
                # normalise trailing whitespace
                suffix = suffix.rstrip() + '\n'
            if sentence:
                if opt_freq:
                    index = sentence.find(softhyphen)
                    if index >= 0:
                        sentence = disambiguateSoftHyphens(sentence, opt_bigrams)
                klen = signs_max_key_len
                while klen:
                    for key, value in signs.iteritems():
                        if len(key) == klen:
                            sentence = sentence.replace(key, value)
                    klen = klen - 1
                if opt_tagged:
                    startDollar = 0
                    while True:
                         nextDollar = sentence.find('$', startDollar)
                         if nextDollar < 0:
                             break
                         replacement = None
                         match = reTaggedCurrency.search(
                             sentence, max(0, nextDollar-4), nextDollar+15
                         )
                         if match:
                             startDollar, endDollar = match.span()
                             replacement = ' %s/$ ' %match.group('CURRENCY')
                             checkAmount = True

                         match = reTaggedCurrencyAndAmount.search(
                             sentence, max(0, nextDollar-4), nextDollar+25
                         )
                         if match:
                             startDollar, endDollar = match.span()
                             replacement = ' %s/$ %s/CRD ' %match.group(
                                 'CURRENCY', 'AMOUNT'
                             )
                         match = reTaggedCurrencyEquation.search(
                             sentence, max(0, nextDollar-4), nextDollar+35
                         )
                         if match:
                             startDollar, endDollar = match.span()
                             newWords = ['']
                             newWords.append('%s/$' %match.group('CURRENCY1'))
                             if match.group('AMOUNT1'):
                                 newWords.append('%s/CRD' %match.group('AMOUNT1'))
                             newWords.append('=/UNC')
                             if match.group('CURRENCY2'):
                                 newWords.append('%s/$' %match.group('CURRENCY2'))
                             newWords.append('%s/CRD' %match.group('AMOUNT2'))
                             newWords.append('')
                             replacement = ' '.join(newWords)
                         if replacement:
                             sentence = sentence[:startDollar] + replacement + sentence[endDollar:]
                             extraDollar = len(replacement)
                         else:
                             extraDollar = 0
                         startDollar = nextDollar + 1 + extraDollar
                else:
                    sentence = sentence.replace('$', '$ ')
                    nextStart = 0
                    while opt_separate_dashes:
                        match = reDashes.search(sentence, nextStart)
                        if not match:
                            break
                        startDash, endDash = match.span()
                        sentence = sentence[:startDash] + ' ' + \
                                   match.group(0) + ' ' + sentence[endDash:]
                        nextStart = endDash+2
                sentence = sentence.replace('  ', ' ')
		sys.stdout.write(prefix)
                sys.stdout.write(sentence)
                sys.stdout.write(suffix)
        if opt_verbose:
            sys.stderr.write('%s: %s lines processed\n' %(filename, lineNo))
            lastStat = now
        if infile != sys.stdin:
            infile.close()

if __name__ == '__main__':
    main()



