#!/usr/bin/env python
# -*- coding: utf-8 -*-

# (C) 2006, 2007, 2008, 2010, 2012, 2013, 2014 Dublin City University
# All rights reserved. This material may not be
# reproduced, displayed, modified or distributed without the express prior written
# permission of the copyright holder.

# Author: Joachim Wagner

# usage: txt2sgml.py <brian.txt >brian.sgml
#
# or     txt2sgml.py my-id-prefix my-file-label tokenise < ... > ...
#
# or     txt2sgml.py --raw < ... > ...
#
# If used as a module, an abbreviation file can be shared with
# txt2sgml.tokenise() to keep full-stops connected to their
# abbreviations.

import base64
import md5
import os
import re
import string
import sys
import xml.sax.saxutils


prefix = 'WMT13-QE-test'
opt_sid_format = '%s.%08d'
opt_count_empty = True
opt_tokenise = False
opt_raw = False
opt_capitalise = False
opt_add_fullstop = False
opt_simple_error_annotation = False
opt_microsoft_mass_noun = False
opt_report = False
opt_remove_duplicates = False
opt_corpus_tag = False
opt_eclass = 'gram'
opt_ignore_sentences_starting_with_period = False
opt_wsj_raw_format = False
opt_gonzaga = False
opt_ignore_multiple_in_gonzaga = False
opt_warn_about_punctuation     = False
opt_exit_after_10th_warning    = False


def writeSentence(sentence, itemNo, errorClass = None, moreAttributes = None):
    global opt_sid_format
    sid = opt_sid_format %(prefix, itemNo)
    m = md5.new(sid)
    m = base64.encodestring(m.digest())[:24]
    sys.stdout.write('<s shuffle=%s id=%s' %(
        xml.sax.saxutils.quoteattr(m),
        xml.sax.saxutils.quoteattr(sid)
    ))
    if errorClass:
        sys.stdout.write(' class=%s' %(
            xml.sax.saxutils.quoteattr(errorClass)
        ))
    if moreAttributes:
        keys = moreAttributes.keys()
        keys.sort()
        for key in keys:
            sys.stdout.write(' %s=%s' %(
                key, xml.sax.saxutils.quoteattr(str(moreAttributes[key]))
            ))
    # We have to escape '<', '>' and '&'.
    text = xml.sax.saxutils.escape(sentence)
    sys.stdout.write('>%s</s>\n' %text)

warningcount = 0

def reportLine(line, lcount, message):
    global warningcount
    sys.stderr.write('Warning: line %d %s\n' %(lcount, message))
    warningcount = warningcount + 1
    if warningcount == 10 and opt_exit_after_10th_warning:
        sys.exit(1)


prefixes = {}
prefixes[0] = 0

def addtodict(s, d):
    d[s] = None
    if len(s) > d[0]:
        d[0] = len(s)

# List of Western style emoticons taken from
# http://en.wikipedia.org/wiki/List_of_emoticons
# + first line: manual additions
s_emoticons = """
:-
:-) :) :o) :] :3 :c) :> =] 8) =) :} :^) :っ) 	
:-D :D 8-D 8D x-D xD X-D XD =-D =D =-3 =3 B^D 	
:-)) 	
>:[ :-( :(  :-c :c :-<  :っC :< :-[ :[ :{ 	
;( 	
:-|| :@ >:( 	
:'-( :'( 	
:'-) :') 	
D:< D: D8 D; D= DX v.v D-': 	
>:O :-O :O 8-0 	
:* :^* ( '}{' ) 	
;-) ;) *-) *) ;-] ;] ;D ;^) :-, 	
>:P :-P :P X-P x-p xp XP :-p :p =p :-Þ :Þ :þ :-þ :-b :b 	
>:\ >:/ :-/ :-. :/ :\ =/ =\ :L =L :S >.< 	
:| :-| 	
:$ 	
:-X :X :-# :# 	
O:-) 0:-3 0:3 0:-) 0:) 0;^) 	
>:) >;) >:-) 	
}:-) }:) 3:-) 3:) 	
o/\o ^5 >_>^ ^<_< 	
|;-) |-O 	
:-& :& 	
#-) 	
%-) %) 	
:-###.. :###.. 	
<:-| 	
ಠ_ಠ 	L
<*)))-{ ><(((*> ><>
\o/
*\0/* 	
@}-;-'--- @>-->--
~(_8^(I)
5:-) ~:-\
//0-0\\
*<|:-)
=:o]
,:-) 7:^]
<3 </3 	
"""

# build prefix lookup table

for s in string.split("""
" `` '' ( ) [ ] { } '
St. EUR USD p.
C'm
"""):
  if s:
    addtodict(s, prefixes)


# build suffix lookup table

suffixes = {}
suffixes[0] = 0
for s in string.split("""
" `` '' ( ) [ ] { }
, . ; : ? !
'll 're 've 'd 'm n't 's '
'LL 'RE 'VE 'D 'M N'T 'S '
not
...
(s)
"""):
  if s:
      addtodict(s, suffixes)

emoticons = {}
emoticons[0] = 0
for s in s_emoticons.split():
    if s:
        addtodict(s, emoticons)
        if s[-1] not in '03578bBcCDILoOpPSvxX':
            addtodict(s, prefixes)
        if s[0]  not in '03578bBcCDILoOpPSvxX':
            addtodict(s, suffixes)

protectedInfixes = {}
protectedInfixes[0] = 0

for s in string.split("""
-
"""):
  if s:
      addtodict(s, protectedInfixes)

symbols = '!"#$%&\'()*+,-./:;<=>?@[\\]^_{|}~'

symbolsForPrefix = ''
symbolsForSuffix = ''
symbolsForInfix = ''
for c in symbols:
    if not prefixes.has_key(c):
        symbolsForPrefix = symbolsForPrefix + c
    if not suffixes.has_key(c):
        symbolsForSuffix = symbolsForSuffix + c
    symbolsForInfix = symbolsForInfix + c

def createReObject(rawsymbols, isForSuffix = 0):
    if not rawsymbols:
        return none
    if rawsymbols[0] == '^':
        # move caret away from start of list
        rawsymbols = rawsymbols[1:] + '^'
    dashpos = rawsymbols.find('-')
    if dashpos > 1:
        # move dash to front
        part1 = rawsymbols[:dashpos]
        part2 = rawsymbols[dashpos+1:]
        rawsymbols = '-' + part1 + part2
    if '\\' in rawsymbols:
        rawsymbols = rawsymbols.replace('\\', '\\\\')
    if ']' in rawsymbols:
        rawsymbols = rawsymbols.replace(']', '\\]')
    expression = '[' + rawsymbols + ']+'
    if isForSuffix:
        expression = expression + '$'
    return re.compile(expression)

reOtherPrefixes = createReObject(symbolsForPrefix, 0)
reOtherSuffixes = createReObject(symbolsForSuffix, 1)
reOtherInfixes  = createReObject(symbolsForInfix,  0)

def expand_token(token, abbrDic = None, depth = 0):
    debug = 0
    if debug: sys.stderr.write('%sexpand_token(%r, ..., %d)\n' %(depth*'\t', token, depth))
    global opt_remove_duplicates
    if not token:
        return []
    length = len(token)
    # split possible prefixes
    global prefixes
    first = []
    slen = prefixes[0]
    while slen > 0:
        if slen > len(token):
            slen = slen - 1
            continue
        prefix = token[:slen]
        if prefixes.has_key(prefix):
            first.append(prefix)
            token = token[slen:]
        slen = slen - 1
    match = reOtherPrefixes.match(token)
    if match:
        start, end = match.span()
        if start != 0:
            raise ValueError, 'unexpected non-zero start index for re.match()'
        if end < len(token):
            prefix = match.group(0)
            first.append(prefix)
            token = token[end:]

    # split possible suffixes
    global suffixes
    last = []
    slen = suffixes[0]
    while slen > 0:
        if slen > len(token):
            slen = slen - 1
            continue
        suffix = token[-slen:]
        if suffixes.has_key(suffix):
            lword = token[:-slen]
            if (suffix == 'not' and lword == 'can') \
            or (not abbrDic or suffix != '.' or not abbrDic.has_key(lword)):
                last = [suffix] + last
                token = lword
        slen = slen - 1
    match = reOtherSuffixes.search(token)
    if match:
        start, end = match.span()
        if end != len(token):
            raise ValueError, 'unexpected end index for re.search()'
        if start > 0:
            suffix = match.group(0)
            lword = token[:-len(suffix)]
            if not abbrDic or suffix != '.' or not abbrDic.has_key(lword):
                last = [suffix] + last
                token = token[:start]

    # recursion
    if debug: sys.stderr.write('%s\t%r, %r, %r\n' %(depth*'\t', first, token, last))
    if len(token) == length:
        if abbrDic and abbrDic.has_key(token[:-1]):
            return [token]
        # check for infixes
        match = reOtherInfixes.search(token)
        if not match:
            return [token]
        start, end = match.span()
        if start == 0 or end == len(token):
            return [token]
        left  = token[:start]
        infix = token[start:end]
        right = token[end:]
        right = expand_token(right, abbrDic, depth + 1)
        protectThisInfix = protectedInfixes.has_key(infix)
        if infix == '.':
            if left[-1] in '0123456789':
                protectThisInfix = True
            if right[0] in '0123456789':
                protectThisInfix = True
        if infix == ':' or infix == ',':
            if left[-1] in '0123456789' and right[0][0] in '0123456789':
                protectThisInfix = True
        if protectThisInfix:
            if debug: sys.stderr.write('%s\tpretected infix %r\n' %(depth*'\t', infix))
            first = left + infix + right[0]
            right = right[1:]
            return [first] + right
        elif abbrDic and infix == '.' and abbrDic.has_key(left):
            if debug: sys.stderr.write('%s\tabbreviation infix %r\n' %(depth*'\t', infix))
            first = left + infix
            return [first] + right
        else:
            if debug: sys.stderr.write('%s\tinfix %r\n' %(depth*'\t', infix))
            left  = expand_token(left,  abbrDic, depth + 1)
            if emoticons.has_key(infix):
                infix = [infix]
            else:
                infix = [infix]
                #infix = expand_token(infix, abbrDic, depth + 1)
            return left + infix + right
    elif depth > 20:
        newTokens = first + [token] + last
    else:
        # TODO: Why not pass abbrDic?
        newTokens = first + expand_token(token, abbrDic, depth + 1) + last
    if True:
        if opt_remove_duplicates:
            tmp = []
            last = None
            for token in newTokens:
                if token != last:
                     tmp.append(token)
                     last = token
            newTokens = tmp
        return newTokens

def get_abbr_dict(file):
    abbrDic = {}
    while True:
        line = file.readline()
        if not line:
            break
        abbrDic[line.rstrip()] = None
    return abbrDic

def tokenise(sentence, abbrDic = None):
    global opt_report
    global punctuation
    tokens = string.split(sentence)
    new_tokens = []
    for token in string.split(sentence):
        report = 0
        for new_token in expand_token(token, abbrDic):
            new_tokens.append(new_token)
            if opt_report and not prefixes.has_key(new_token) and not suffixes.has_key(new_token):
                for c in '\'",.;:?!()[]{}%&/':
                    if c in new_token:
                        report = 1
                        break
        if opt_report:
            sys.stderr.write('Warning: problematic token %s\n' %`token`)
            if token == '&&':
                sys.stderr.write('\t%s\n' %sentence)
    return string.join(new_tokens)

def main():
  global prefix
  global opt_eclass
  global opt_tokenise
  global opt_raw
  opt_abbr_dict = None
  while len(sys.argv) > 1 and sys.argv[1][:2] == '--':
      arglen = 1
      if sys.argv[1] == '--':
          del sys.argv[1]
          break
      elif sys.argv[1] == '--abbr':
          filename = sys.argv[2]
          file = open(filename, 'rb')
          opt_abbr_dict = get_abbr_dict(file)
          file.close()
          arglen = 2
      elif sys.argv[1] == '--raw':
          opt_raw      = True
          opt_tokenise = True
      elif sys.argv[1] == '--verbose':
          opt_verbose  = True
      elif sys.argv[1] == '--help':
          usage()
          sys.exit(0)
      else:
          sys.stderr.write('unknown option %s\n' %`sys.argv[1]`)
          sys.exit(1)
      for i in range(arglen):
          del sys.argv[1]
  # old command line formats
  if len(sys.argv) > 1:
      prefix = sys.argv[1]
  if len(sys.argv) > 2:
      opt_eclass = sys.argv[2]
  if len(sys.argv) > 3 and sys.argv[3] == 'tokenise':
      opt_tokenise = True
  lcount = 0
  icount = 1
  inExamples = 0
  while 1:
    line = sys.stdin.readline()
    if not line:
        break
    lcount = lcount + 1
    sentence = string.rstrip(line)
    if opt_wsj_raw_format and sentence in ('', '.START'):
        continue
    if not sentence:
        reportLine(line, lcount, 'empty sentence ')
        if opt_count_empty:
            icount = icount + 1
        continue
    if opt_corpus_tag \
    and sentence[0] == '<' \
    and sentence[-1] == '>':
        # Corpus tag
        prefix = sentence[1:-1]
        icount = 1
        continue
    if sentence[0] == '.' and opt_warn_about_punctuation:
        reportLine(line, lcount, 'sentence starts with punctuation')
        if opt_ignore_sentences_starting_with_period:
            continue
    if opt_add_fullstop and sentence[-1] not in '.!?':
        sentence = sentence + '.'
    if opt_simple_error_annotation:
        eclass = 'gram'
        tokens = sentence.split()
        first = tokens[0]
        if first == '?':
            eclass = 'questionable'
            sentence = ' '.join(tokens[1:])
        elif first[0] == '*':
            eclass = first[1:]
            sentence = ' '.join(tokens[1:])
    elif opt_gonzaga:
        fields = line.split('\t')
        if len(fields) < 5:
            reportLine(line, lcount, 'not enough fields')
            continue
        if fields[0] == 'Expression' and fields[1] == 'Level':
            reportLine(line, lcount, 'ignoring header')
            continue
        sentence = fields[0]
        level    = fields[1]
        language = fields[2]
        context  = fields[3]
        topic    = fields[4].rstrip()
        if opt_capitalise:
            sentence = sentence.capitalize()
        if opt_ignore_multiple_in_gonzaga:
            scount = 0
            for char in '.?!':
                scount = scount + sentence.count(char)
            if scount > 1:
                continue
        writeSentence(tokenise(sentence, opt_abbr_dict), lcount, 'UNGRAM', {
            #'row': lcount,
            'level': level,
            'language': language,
            'context': context,
            'topic': topic,
        })
        icount = icount + 1
        continue
    elif opt_microsoft_mass_noun:
        fields = line.split('\t')
        if len(fields) < 4:
            reportLine(line, lcount, 'not enough fields')
            continue
        if fields[1] == 'URL':
            reportLine(line, lcount, 'ignoring header')
            continue
        word = fields[0]
        reference = fields[1]
        sentence = fields[2]
        if opt_capitalise:
            sentence = sentence.capitalize()
        writeSentence(tokenise(sentence, opt_abbr_dict), icount, 'UNGRAM', {
            'word': word,
            'ref':  reference,
            'align': lcount,
        })
        icount = icount + 1
        while len(fields) > 3:
            sentence = fields[3]
            if opt_capitalise:
                sentence = sentence.capitalize()
            writeSentence(tokenise(sentence, opt_abbr_dict), icount, 'gram', {
                'word': word,
                'ref':  reference,
                'align': lcount,
            })
            icount = icount + 1
            del fields[3]
        continue
    else:
        eclass = opt_eclass
    if opt_capitalise:
        sentence = sentence.capitalize()
    if opt_tokenise:
        sentence = tokenise(sentence, opt_abbr_dict)
    if opt_raw:
        sys.stdout.write(sentence)
        sys.stdout.write('\n')
    else:
        writeSentence(sentence, icount, eclass)
    icount = icount + 1

testdata = """*=aaa -aaa *aaa
=-=-=aaa
aaa=-=-=
=-=-=aaa=-=-=
((( (( (
(a (aa (aaa
((a ((aa ((aaa
(((a (((aa (((aaa
http://a.b.c/
``Hello World!''
=-=``Hello World!''=-=
abc''!
"neutral"
#hash
@name
#abc''!@@
Yes!!!
aaav.v
aa=v.v
v.v=aa
5678)
8)123
8)!
:-)
:)
aa8)123
aa8)!
aa:-)
aa:)
8)123aa
8)!aa
:-)aa
:)aa
"""

if __name__ == '__main__':
    main()
    for token in []: # testdata.split():
        expansion = expand_token(token, None, 0)
        print '%20s --> %d items:\t%s' %(token, len(expansion), '\t'.join(expansion))

