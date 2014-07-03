# -*- coding: utf-8 -*-
import os
import sys

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))
# f = open(os.path.join(__location__, 'bundled-resource.jpg'))
#Loading the Sentiment Lexicon in the dictionary
lex={}
f1=open(os.path.join(__location__, "merge.csv")).readlines()
for i in f1:
	temp = i.split(",")	
	temp[1] = temp[1].strip("\n")
	lex[temp[0].lower()]=temp[1]

#Loading the Emoticons Lexicon in the dictionary
elex={}
f2=open(os.path.join(__location__, "emoticon.csv")).readlines()
for i in f2:
	temp = i.split(",")	
	temp[1] = temp[1].strip("\n")
	elex[temp[0].lower()]=temp[1]


#Function for calculating tweet score
def calculateScore(sentence):
	 #performing whitespace tokenization	
	readLine = sentence.split()
	emoticon_score,lexical_score,lex_match,elex_match = 0.0,0.0,0,0
	pos_score,neg_score,epos_score,eneg_score = 0.0,0.0,0.0,0.0
	cpos,cneg,cneu = 0,0,0
	try:
		for z,tok in enumerate(readLine):
			#scoring polar words in the sentence
			tok = tok.lower()
			if(lex.has_key(tok)):
				lex_match += 1	
				negCheck = checkForNegation(sentence,z)
				if float(lex[tok]) > 0.0:
					if negCheck == 0:
						pos_score = pos_score + float(lex[tok])
						cpos = cpos+1
					else:
						neg_score = neg_score - float(lex[tok])
				elif float(lex[tok]) < 0.0:
					if negCheck == 0:
						cneg = cneg+1
						neg_score = neg_score + float(lex[tok])
					else:
						pos_score = pos_score - float(lex[tok])

			#scoring emoticons in the sentence
			elif elex.has_key(tok):
				elex_match += 1
				if elex[tok] > 0.0:
					epos_score = epos_score + float(elex[tok])
				elif elex[tok] < 0.0:
					eneg_score = eneg_score + float(elex[tok])

		#averaging scores for complete sentence
		if elex_match!=0:
    	   	 	emoticon_score = ((epos_score+eneg_score)/elex_match)
    		if lex_match!=0:
        		lexical_score = ((pos_score+neg_score)/lex_match)/4.0

	    	ans=emoticon_score+lexical_score
    		if elex_match != 0 and lex_match != 0:
        		ans = ans/2.0
 	   	return ans

  	except KeyError:
		return 0

#Negation Handling
def checkForNegation(sentence,index):
  #Window for looking for Negators-> negativity indicators
	window = 2
	negativeWordsList = {'not':'1','no':'1','never':'1','n\'t':'1'}
	readLine = sentence.split()
	try:
		for i in range(index-window,index+window+1, 1):
		      if negativeWordsList.has_key(readLine[i].lower()):
		        return 1 	
	except:
    		pass
	return 0



def ruleScorer(sentence):	
	score = calculateScore(sentence)
	return score #score range{-1,1}

#if __name__ == "__main__":
#	main()

   	
		
