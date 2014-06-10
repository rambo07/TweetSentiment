import os;
import sys;


def calculateScore(sentence, lexicon):
  readLine = sentence.split();
  lex = lexicon;
  pos_score =0.0;
  neg_score =0.0;
  for z in readLine:
    if(lex.has_key(z.lower())):
      if(lex[z.lower()] > 0.0):
        pos_score = pos_score + float(lex[z.lower()]);
      elif(lex[z] < 0.0):
	neg_score = neg_score + float(lex[z.lower()]);
  return (pos_score - neg_score); 

'''def checkForNegation(sentence,index):
  window = 2;
  negativeWordsList = {'not':1,'no':1,'never':1,'n\'t':1}
  readLine = sentence.split();
  try{
     for i in range(index-window,index+window+1,1) 
	  if(i!=index)
	    if(negativeWordList.has_key(readLine[i].lower()))
              return 1; 		
  }
  except{
	continue;
  }
  return 0;
'''
 
def main():
  inputFile = sys.argv[1];
  lexicon = sys.argv[2];
  lex = {};
  threshols = 0.0;
  countPos=0;countNeg=0;countNeu=0;
  countPosScore=0;countNegScore=0;countNeuScore=0;
  
#Loading the lexicon file in a dictionary
  f1=open(lexicon).readlines();
  for i in f1:
    temp = i.split(",");	
    temp[1] = temp[1].strip("\n");
    lex[temp[0].lower()]=temp[1];
  
#Reading tweets from a file sequentially
  f2 = open(inputFile).readlines();
  for j in f2:
    sen=j.strip("\n");
    print "Tweet-----",sen;
    score = calculateScore(sen,lex);
#    negCheck = checkForNegation(sen,j);
    if(negCheck!=0)
	score = -score;

#Deciding the tweet polarity 
    if( score > threshold):
       countPos = countPos+1;	
       countPosScore = countPosScore+score;	
       print "Polarity-----Positive Tweet" 
    elif( score < threshold):
       countNeg = countNeg+1;	
       countNegScore = countNegScore+score;	
       print "Polarity-----Negative Tweet"
    else:
       countNeu = countNeu+1;	
       countNeuScore = countNeuScore+score;	
       print "Polarity-----Neutral"	 
  print countPos, countNeg, countNeu;

if __name__ == "__main__":
  main();

   	
		
