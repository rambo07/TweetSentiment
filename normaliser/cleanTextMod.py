#!/usr/bin/env python

# Input: a file containing one sentence per line, a list of one-to-one word mappings,
#a list of many-to-one word mappings and a list of emoticons
# Output: stdout, a cleaner version of each sentence
import sys
import re

def normaliseCase(sentence):
        '''change all words sequences of length > 2 that consist of lowercase characters to lowercase. Make sure that a sentence starts with an uppercase character'''
        new_sentence = ""
        words = sentence.split()
        count = 0
        while count < len(words):
                if count+1 < len(words):
                        if words[count].isupper() and words[count+1].isupper():
                                index = count
                                while index < len(words) and words[index].isupper():
                                        new_sentence = new_sentence + " " + words[index].lower()
                                        index = index + 1
                                count = index
                        else:
                                new_sentence = new_sentence + " " + words[count]
                                count = count + 1
                else:
                        new_sentence = new_sentence + " "  + words[count]
                        count = count + 1
        new_sentence = new_sentence.strip()
        if new_sentence[0:1].islower():
                new_sentence = new_sentence[0:1].upper() + new_sentence[1:]
        return new_sentence

def replaceEmoticons(sentence,emoticonList):
        '''replace emoticons with full stops or commas depending on their position within the sentence'''
        words = sentence.split()
        new_sentence = ""
        word_count = 0
        for word in words:
                if isEmoticon(word,emoticonList) and word_count+1 == len(words):
                        new_sentence = new_sentence + " " + "."
                elif isEmoticon(word,emoticonList) and word_count == 0:
                        new_sentence = new_sentence
                elif isEmoticon(word,emoticonList):
                        new_sentence = new_sentence + " " + ","
                else:
                        new_sentence = new_sentence + " " + word
                        word_count = word_count + 1
        return new_sentence.strip()

def isEmoticon(token,emoticonList):
        '''returns true if the token is in the list of emoticons, false otherwise'''
        return token in emoticonList

def replaceEmailsAndUrls(sentence):
        '''replace emails, urls and mentions with generic tokens "EmailAddress", "LinkAddress" and "Mention"'''
        new_sentence = ""
        words = sentence.split()
        for word in words:
                if word.startswith("http"):
                        #fix tokenisation bug
                        if ".html" in word and not word.endswith(".html"):
                                index = word.find(".html")
                                new_sentence = new_sentence + " LinkAddress " + word[index+5:]
                        else:
                                new_sentence = new_sentence + " LinkAddress"
                elif "@" in word and "." in word:
                        #fix tokenisation bug
                        if ".com" in word and not word.endswith(".com"):
                                index = word.find(".com")
                                new_sentence = new_sentence + " EmailAddress  " + word[index+4:]
                        else:
                                new_sentence = new_sentence + " EmailAddress"
                #elif word.startswith("@") or word.startswith("#"):
                #        new_sentence = new_sentence + " " + word[1:]
                else:
                        new_sentence = new_sentence + " " + word
        return new_sentence.strip()

def normaliseQuotes(sentence):
        '''replace " with `` or '' depending on position'''
        new_sentence = ""
        sentence = sentence.replace("& quot ;","\"")
        if sentence.startswith('"'):
                sentence = "``" + sentence[1:]
        if sentence.endswith('"'):
                sentence = sentence[:-1] + "''"
        words = sentence.split()
        count = 0
        while count < len(words):
                word = words[count]
                if word == "\"":
                        new_sentence = new_sentence + " ``"
                        index = count+1
                        while index < len(words) and words[index] != "\"":
                                new_sentence = new_sentence + " " + words[index]
                                index = index + 1
                        if index < len(words):
                                new_sentence = new_sentence + " ''"
                        count = index+1
                else:
                        new_sentence = new_sentence + " " + word
                        count = count + 1 
        return new_sentence.strip()

def replaceWords(sentence,wordDict):
        '''perform all the word replacements specified in the word list'''
        new_sentence = ""
        words = sentence.split()
        #special case for the first word in the sentence
	if len(words) == 0:
		return sentence
        firstWord = words[0]
        if len(firstWord) > 1:
                wordToLookUp = firstWord[0:1].lower() + firstWord[1:]
                if wordToLookUp in wordDict.keys():
                        new_sentence = wordDict[wordToLookUp][0:1].upper() + wordDict[wordToLookUp][1:]
                else:
                        new_sentence = firstWord
        else:
                wordToLookUp = firstWord.lower()
                if wordToLookUp in wordDict.keys():
                        new_sentence = wordDict[wordToLookUp].upper()
                else:
                        new_sentence = firstWord
        for word in words[1:]:
                if word in wordDict.keys():
                        new_sentence = new_sentence + " " + wordDict[word] 
                else:
                        new_sentence = new_sentence + " " + word
        return new_sentence.strip()


def normalisePunctuation(sentence):
        '''replace things like !!!!???? with ?'''
        new_sentence = re.sub(r'[ \!\.\?]*\?',r" ?",sentence) 
        new_sentence = re.sub(r'[ \!\\.?]*\!',r" !",new_sentence)
        new_sentence = re.sub(r'[\?\!][ \!\\.?]*\.',r" .",new_sentence)
        new_sentence = re.sub(r'\.\.\.\.[\.]*',r"...",new_sentence)
        new_sentence = re.sub(r' \. \.[ \.]*',r" ...",new_sentence)
        return new_sentence

def miscellaneous(sentence):
        '''miscellaneous replacements determined from looking at the unlabelled data'''
        new_sentence = sentence.replace("b / c","because")
        new_sentence = new_sentence.replace("a / c","air conditioning")
        new_sentence = new_sentence.replace("j / k","just kidding")
        new_sentence = new_sentence.replace("wan na","want to")
        return new_sentence

inputFilename = sys.argv[1]
emoticonFilename = sys.argv[2]
emoticonFile = open(emoticonFilename)
emoticonList = []
while True:
        line = emoticonFile.readline()
        if not line:
                break
        emoticonList.append(line[:-1])

one2oneWordListFilename = sys.argv[3]
one2oneWordListFile = open(one2oneWordListFilename)
one2oneWordDict = dict()
while True:
        line = one2oneWordListFile.readline()
        if not line:
                break
        words = line.split(',')
        oldWord = words[0]
        newWord = words[1]
        one2oneWordDict[oldWord] = newWord

one2manyWordListFilename = sys.argv[4]
one2manyWordListFile = open(one2manyWordListFilename)
one2manyWordDict = dict()
while True:
        line = one2manyWordListFile.readline()
        if not line:
                break
        words = line.split(',')
        oldWord = words[0]
        newWord = words[1][:-1]
        one2manyWordDict[oldWord] = newWord
                                                    
if inputFilename == '-':
    inputFile = sys.stdin
else:
    inputFile = open(inputFilename);
while True:
        line = inputFile.readline()
        if not line:
                break

        sentence = line[:-1]

        if True:
                # normalise case
                sentence = normaliseCase(sentence)
        
                # handle emoticons
                sentence = replaceEmoticons(sentence,emoticonList)

                # replace emails, mentions and urls
                sentence = replaceEmailsAndUrls(sentence)
        
                # fix quotes
                sentence = normaliseQuotes(sentence)

                # one-to-one word mappings
                sentence = replaceWords(sentence,one2oneWordDict)

                # many to one mapping
                sentence = replaceWords(sentence,one2manyWordDict)

                # repeated punctuation
                sentence = normalisePunctuation(sentence)

                # miscellaneous, ad-hoc stuff
                sentence = miscellaneous(sentence)

                print sentence


