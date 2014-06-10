import os;
import sys;

#Loading the Sentiment Lexicon in the dictionary
lex={};
f1=open("merge.csv").readlines();
for i in f1:
  temp = i.split(",");	
  temp[1] = temp[1].strip("\n");
  lex[temp[0].lower()]=temp[1];

#Function for calculating tweet score
def calculateScore(sentence):
  readLine = sentence.split();
  pos_score =0.0;
  neg_score =0.0;
  for z in range(0,len(readLine),1):
    token = readline[z].lower();
    if(lex.has_key(token)):
#      checkForNegation(sentence,z)
      if(lex[token] > 0.0):
        pos_score = pos_score + float(lex[token]);
      elif(lex[token] < 0.0):
	neg_score = neg_score + float(lex[token]);
  return (pos_score - neg_score); 

'''def checkForNegation(sentence,index):
  window = 2;
  negativeWordsList = {'not':1,'no':1,'never':1,'n\'t':1}
  readLine = sentence.split();
  try:
     for i in range(index-window,index+window+1,1): 
	  if(i!=index):
	    if(negativeWordList.has_key(readLine[i].lower())):
              return 1; 		
  except:
	continue;
  return 0;
'''
 
def ruleScorer(sentence):
  score = calculateScore(sentence); 
  return score;
  
if __name__ == "__main__":
  main();

   	
		
