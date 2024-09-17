# -*- coding: utf-8 -*-
"""auto pacer.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1GFMPYmjGa8Fz8nioooGfti9T5AsC9q_e

*italicized text*
"""

#Imports
!pip install youtube_transcript_api

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import JSONFormatter
import string
import matplotlib.pyplot as plt
from gensim import corpora
from gensim.models import LdaModel
from pprint import pprint
from gensim.parsing.preprocessing import preprocess_string
from gensim import models
from gensim import similarities
import numpy as np
from gensim.models.coherencemodel import CoherenceModel
from textwrap import indent
import json

#Get transcript

transcript = YouTubeTranscriptApi.get_transcript("I3GWzXRectE", languages=['en'])
#transcript = YouTubeTranscriptApi.get_transcript("lZ3bPUKo5zc", languages=['en'])


#remove unicode chars
for d in transcript:
  d['text'] = d['text']
  d['text'] = d['text'].replace(u'\xa0', u' ')


# Combining multiple sentences from transcript

combined_transcript = []

for i in range(0, len(transcript), 3):
    # Check if there are three consecutive segments available
    if i + 2 < len(transcript):
        # Combine the text of three consecutive segments
        combined_text = transcript[i]['text'] + transcript[i + 1]['text'] + transcript[i + 2]['text']

        # Calculate the combined duration and start time
        combined_duration = transcript[i]['duration'] + transcript[i + 1]['duration'] + transcript[i + 2]['duration']
        combined_start = transcript[i]['start']


        combined_segment = {
            'text': combined_text,
            'duration': combined_duration,
            'start': combined_start
        }


        combined_transcript.append(combined_segment)

    # If there are only two consecutive segments available
    elif i + 1 < len(transcript):

        combined_text = transcript[i]['text'] + transcript[i + 1]['text']


        combined_duration = transcript[i]['duration'] + transcript[i + 1]['duration']
        combined_start = transcript[i]['start']


        combined_segment = {
            'text': combined_text,
            'duration': combined_duration,
            'start': combined_start
        }


        combined_transcript.append(combined_segment)

    #  Single segment
    else:

        combined_transcript.append(transcript[i])

# preprocess each segment and add the clean, tokenized list of segment to texts array

texts = []

for segment in combined_transcript:
  text = segment['text']
  texts.append(preprocess_string(text))

# Create dictionary and document-term matrix
dictionary = corpora.Dictionary(texts)
corpus = [dictionary.doc2bow(doc) for doc in texts]

#  Sum positive proportions of each corpus
def sumProportions(corpus):
  a = []
  for docTuple in corpus:
    total = sum(t[1] for t in docTuple if t[1] > 0)
    a.append(total)

  return a

#LSI TRAINING: finding optimal topic count

coherenceScores = []
topicCount = []

for k in range(3, 10):

  tfidf = models.TfidfModel(corpus)
  corpus_tfidf = tfidf[corpus]

  lsi_model = models.LsiModel(corpus=corpus_tfidf,
                                  id2word=dictionary,
                                  num_topics=k)

  coherence_model = CoherenceModel(model=lsi_model,
                                              texts=texts,
                                              corpus=corpus,
                                              dictionary=dictionary,
                                              coherence='c_v')
  coherenceScores.append(coherence_model.get_coherence())
  topicCount.append(k)

#Set optimal topics

optimal_index = coherenceScores.index(max(coherenceScores))
optimalTopics = topicCount[optimal_index]

#LSI TRAINING with optimal Topic Count

lsi_model = models.LsiModel(corpus=corpus_tfidf,
                                  id2word=dictionary,
                                  num_topics=optimalTopics)

corpus_lsi = lsi_model[tfidf[corpus]]
pprint(lsi_model.print_topics())
# Sum positive proportions of each topic for each doc: shows how on topic the doc is
proportionSum = sumProportions(corpus_lsi)

# Using proportion sum of each doc, find threshold such that 20% percent of docs in proportion sum are below it

propArr = np.array(proportionSum)

threshold = np.percentile(propArr, 20)
print(threshold)
# Plot the frequency counts
#plt.hist(propArr, edgecolor='black', bins=[0,threshold,np.max(propArr)])
#plt.hist(propArr)

#Finally, print each segment in transcript. Prints the proportions if segment is on topic
for i, (doc, v) in enumerate(zip(combined_transcript ,corpus_lsi)):


  if proportionSum[i] >= threshold:
    # Printing proportions -- on topic
    print(f"\n{doc['text']} {v}\n")

  else:
    # No proportions -- off topic
    print(f"\n{doc['text']}\n")