#!/usr/bin/env python
# -*- coding: utf-8 -*-

# (C) 2006, 2007, 2013 Dublin City University
# All rights reserved. This material may not be
# reproduced, displayed, modified or distributed without the express prior written
# permission of the copyright holder.

# Author: Joachim Wagner

""" Takes the string between first and last SGML tag on each line,
    converts Unicode left and right quotes to `` and '',
    and optionally disambiguates neutral quotes (").

    Options --anywhere and --separate are recommended if input is not
    already tokenised. (Running txt2sgml.py first is not a good idea
    as the latter only supports basic quotes.)
"""

import bz2
import gzip
import random
import re
import string
import sys
import time

left_quote  = u'\N{left double quotation mark}'.encode('utf-8')
right_quote = u'\N{right double quotation mark}'.encode('utf-8')

# supported quotes: `` '' " U+201C U+201D

reAnyQuote = re.compile(
    """(?P<QUOTE>(``)|('')|(")|(%s)|(%s))""" %(left_quote, right_quote)
)

reAnyQuoteToken = re.compile(
    """ (?P<QUOTE>(``)|('')|(")|(%s)|(%s)) """ %(left_quote, right_quote)
)

reAnyQuoteTaggedToken = re.compile(
    """ (?P<QUOTE>(``)|('')|(")|(%s)|(%s))/PUQ """ %(left_quote, right_quote)
)

quote2side = {
    # if changes are necessary, please consider implementing
    # command line options --[add|delete]-[left|right|neutral]-input-quote
    # see --left and --right for a template
    "``": -1,
    "''": 1,
    '"': 0,
    left_quote: -1,
    right_quote: 1,
}

side2quote = {
    # These quotes are used in the output.
    # They can be overridden with command line options.
    -1: "``",
    1:  "''",
}


reNextToken = re.compile('(?P<WORD>[^ ]+)/(?P<POS>[A-Z0-9-]+) ')
reTag = re.compile('/(?P<POS>[A-Z0-9-]+) ')

reAnyQuoteFinal = re.compile(
    """((``)|('')|(")|(%s)|(%s))$""" %(left_quote, right_quote)
)

def disambiguate_quotes(sentence, reQuote, insertSpace = True,
    tagged = False, allowUNC = False, strip = None
):
    global quote2side
    global side2quote
    global reNextToken
    global reAnyQuoteFinal
    level = 0
    start = 0
    while 1:
        match = reQuote.search(sentence, start)
        if not match:
            return sentence
        start, end = match.span()
        quote = match.group('QUOTE')
        side = quote2side[quote]
        if not side:
            # neutral quote
            if level:
                side = 1
            else:
                side = -1
        quote = side2quote[side]
        level = level - side
        if level < 0:
            level = 0
        startQuote, endQuote = match.span('QUOTE')
        if insertSpace and tagged:
            # We cannot insert space to the left as we don't know
            # how to tag the new token.
            # To the right, we only separate if the quote will be
            # standing alone.
            if sentence[startQuote-1] == ' ':
                # handle case ``Of/X
                match = reNextToken.search(sentence, endQuote, endQuote+80)
                if match and match.start() == endQuote:
                    nextPOS = match.group('POS')
                    separated = True
                    if nextPOS != 'PUQ':
                        quote = quote + '/PUQ '
                    elif reAnyQuoteFinal.match(match.group('WORD')):
                        quote = quote + '/PUQ '
                    elif allowUNC:
                        startNextPOS, endNextPOS = match.span('POS')
                        sentence = sentence[:startNextPOS] + 'UNC' + sentence[endNextPOS:]
                        quote = quote + '/PUQ '
                    else:
                        separated = False
                    if separated and strip and sentence[endQuote] == strip:
                        endQuote = endQuote + 1
            else:
                # handle case .''/X
                # 1. make sure there is only a tag to the right
                match = reTag.match(sentence, endQuote)
                # 2. test for punctuation on the left
                leftContext = sentence[:startQuote]
                startWord = leftContext.rfind(' ')
                if startWord < 0:
                    startWord = -1
                word = sentence[startWord+1:startQuote]
                if match and word in ('.', '!', '?', '...', ';', ':'):
                    endQuote = match.end()
                    quote = '/PUN ' + quote + '/PUQ '
        elif insertSpace:
            if sentence[startQuote-1] != ' ':
                quote = ' ' + quote
                if strip and sentence[startQuote-1] == strip:
                    startQuote = startQuote - 1
            if sentence[endQuote] != ' ':
                quote = quote + ' '
                if strip and sentence[endQuote] == strip:
                    endQuote = endQuote + 1
        sentence = sentence[:startQuote] + quote + sentence[endQuote:]
        start = startQuote + len(quote)
    return sentence



def usage():
    sys.stderr.write("Usage:")
    sys.stderr.write(' %s [options] [*.cinput|*.sgml[.gz|.bz2]]\n' %sys.argv[0])
    sys.stderr.write('Options:\n')
    sys.stderr.write('\t--anywhere    also substitute quotes appearing within tokens\n')
    sys.stderr.write('\t              (default: only stand alone quotes are touched)\n')
    sys.stderr.write('\t--separate    add space to separate quotes from tokens\n')
    sys.stderr.write('\t              (no effect if --anywhere is not specified;\n')
    sys.stderr.write('\t              with --tagged, only quotes at start of word\n')
    sys.stderr.write('\t              can be separated as we have to tag each token)\n')
    sys.stderr.write('\t--tagged      support brown-style annotation/NN\n')
    sys.stderr.write('\t--strip C     strip away character C from separated word\n')
    sys.stderr.write('\t              (useful to remove MWU delimiter)\n')
    sys.stderr.write('\t--allow-UNC   even separate if rigth word has /PUQ tag\n')
    sys.stderr.write('\t--header      output <file name="..."> for each file\n')
    sys.stderr.write('\t--left  <str> output left  quotes as str (default: ``)\n')
    sys.stderr.write('\t--right <str> output right quotes as str (default: \'\')\n')
    sys.stderr.write('\t--verbose     output progress info to stderr\n')
    #sys.stderr.write('\t--quiet       do not output progress info\n')
    sys.stderr.write('\t--raw         read and write plain text (default: sgml)\n')
    sys.stderr.write('\t--help        print this message\n')


def main():
    global side2quote
    global reAnyQuote
    global reAnyQuoteToken
    opt_anywhere       = False
    opt_separateQuotes = False
    opt_tagged         = False
    opt_header         = False
    opt_verbose        = False
    opt_allow_unc      = False
    opt_strip          = None
    opt_raw            = False
    while len(sys.argv) > 1 and sys.argv[1][:1] == '-':
        arglen = 1
        if sys.argv[1] == '--':
            del sys.argv[1]
            break
        elif sys.argv[1] == '--anywhere':
            opt_anywhere       = True
        elif sys.argv[1] == '--separate':
            opt_separateQuotes = True
        elif sys.argv[1] == '--tagged':
            opt_tagged         = True
        elif sys.argv[1] == '--raw':
            opt_raw            = True
        elif sys.argv[1] in ('--allow-unc', '--allow-UNC'):
            opt_allow_unc      = True
        elif sys.argv[1] == '--header':
            opt_header         = True
        elif sys.argv[1] == '--verbose':
            opt_verbose        = True
        elif sys.argv[1] == '--quiet':
            # that's the default now
            opt_verbose        = False
        elif sys.argv[1] == '--strip':
            opt_strip          = sys.argv[2]
            arglen = 2
        elif sys.argv[1] == '--left':
            side2quote[-1] = sys.argv[2]
            arglen = 2
        elif sys.argv[1] == '--right':
            side2quote[1]  = sys.argv[2]
            arglen = 2
        elif sys.argv[1][:3] in ('--h', '-h', '-he'):
            usage()
            sys.exit(0)
        else:
            sys.stderr.write('unknown option %s\n' %`sys.argv[1]`)
            sys.exit(1)
        for i in range(arglen):
            del sys.argv[1]
    if len(sys.argv) < 2:
        # no file provided on command line
        # -> add None to the file list to mark reading from stdin
        sys.argv.append(None)
    if opt_anywhere:
        reQuote = reAnyQuote
    elif opt_tagged:
        reQuote = reAnyQuoteTaggedToken
    else:
        reQuote = reAnyQuoteToken
    lastStat = 0.0
    for filename in sys.argv[1:]:
        if filename is None:
            infile = sys.stdin
        elif filename[-4:] == '.bz2':
            infile = bz2.BZ2File(filename, 'rb')
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
		added_space_left  = False
                added_space_right = False
                if True: # not opt_anywhere:
                    if sentence[0] != ' ':
                        sentence = ' ' + sentence
                        added_space_left = True
                    if sentence[-1] != ' ':
                        sentence = sentence + ' '
                        added_space_right = True
                sentence = disambiguate_quotes(
                    sentence,
                    reQuote,
                    opt_separateQuotes,
                    opt_tagged, opt_allow_unc,
                    opt_strip
                )
                if added_space_left:
                    sentence = sentence[1:]
                if added_space_right:
                    sentence = sentence[:-1]
		sys.stdout.write(prefix)
                sys.stdout.write(sentence)
                sys.stdout.write(suffix)
        if opt_verbose:
            sys.stderr.write('%s: %s lines processed\n' %(filename, lineNo))
            lastStat = time.time()
        if infile != sys.stdin:
            infile.close()

if __name__ == '__main__':
    main()



