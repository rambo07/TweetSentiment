TweetSentiment
==============

This code predicts the polarity scores for an input sentence.
It is developed for scoring sentiments in tweets in English language.
It's a rule based approach which searches the words in a sentence in a dictionary of polar words and score the words accordingly.
Emoticons are searched in emoticon dictionary compiled form wikipedia. For each sentence/tweet a final score between {-1,1} is retrieved using
the sentiment lexicon and emoticon dictionary.
The algorithm perform Negation handling in a window of 2 and can be configured based on the requirements.
