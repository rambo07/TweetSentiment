# -*- coding: utf-8 -*-
import os;
import sys;

#Loading the Sentiment Lexicon in the dictionary
lex={};
f1=open("merge.csv").readlines();
for i in f1:
  temp = i.split(",");	
  temp[1] = temp[1].strip("\n");
  lex[temp[0].lower()]=temp[1];

#Loading the Emoticons Lexicon in the dictionary
elex={};
f2=open("emoticon.csv").readlines();
for i in f2:
  temp = i.split(",");	
  temp[1] = temp[1].strip("\n");
  elex[temp[0].lower()]=temp[1];


#Function for calculating tweet score
def calculateScore(sentence):
  #performing whitespace tokenization	
  readLine = sentence.split();
  emoticon_score=0.0;lexical_score=0.0;lex_match=0;elex_match=0;
  pos_score = 0.0; neg_score = 0.0;
  epos_score = 0.0; eneg_score = 0.0;
  cpos = 0; cneg = 0; cneu=0;
  try:
    for z in range(0,len(readLine),1):
      token = readLine[z].lower();
      if(lex.has_key(token)):
        lex_match += 1	
        negCheck = checkForNegation(sentence,z)
        if(float(lex[token]) > 0.0):
	  if(negCheck == 0):	
            pos_score = pos_score + float(lex[token]);
	    cpos = cpos+1;
	  else:
            neg_score = pos_score + float(lex[token]);
        elif(float(lex[token]) < 0.0):
	  if(negCheck == 0):	
	    cneg = cneg+1;
	    neg_score = neg_score + float(lex[token]);
	  else:
	    pos_score = neg_score + float(lex[token]);
      elif(elex.has_key(token)):
        elex_match += 1	
        if(elex[token] > 0.0):
          epos_score = epos_score + float(elex[token]);
        elif(elex[token] > 0.0):
          eneg_score = eneg_score + float(elex[token]);
    if(elex_match!=0):
	emoticon_score=((epos_score-eneg_score)/elex_match);
    if(lex_match!=0):	
        lexical_score = ((pos_score-neg_score)/lex_match)/4.0

    ans=emoticon_score+lexical_score;	
    if(elex_match!=0 and lex_match!=0):	
	ans = ans/2.0
    return ans;	

  except:
    return 0;	

#Negation Handling
def checkForNegation(sentence,index):
  window = 2;	#Window for looking for Negators-> negativity indicators
  negativeWordsList = {'not':'1','no':'1','never':'1','n\'t':'1'}
  readLine = sentence.split();
  try:
    for i in range(index-window,index+window+1,1):   
      if(negativeWordsList.has_key(readLine[i].lower())):
        return 1; 	
  except:
    return 0;

 
def ruleScorer(sentence):
  score = calculateScore(sentence); 
  return score; #score range{-1,1}

if __name__ == "__main__":
  main();

   	
		
