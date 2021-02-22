# -*- coding: utf-8 -*-
"""BD_HW2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1kBfvqdorS4d_g9vajWPiPAUBEzSi8urd

# **TEXT CLUSTERING USING KMEANS AND DIMENSIONALITY REDUCTION**


---

## Importing libraries, loading the dataset, defining functions
"""

from google.colab import drive
import time
import numpy as np
import random
import operator

import sklearn
from sklearn.feature_extraction.text import HashingVectorizer, TfidfVectorizer
from sklearn.cluster import MiniBatchKMeans, KMeans
from sklearn import metrics
from sklearn.decomposition import TruncatedSVD, PCA
from sklearn.preprocessing import Normalizer
from sklearn.pipeline import make_pipeline
from sklearn.metrics import pairwise_distances_argmin_min

import nltk
from nltk.stem import WordNetLemmatizer 

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import wordcloud
from wordcloud import WordCloud

nltk.download('wordnet')
nltk.download('omw')
nltk.download('punkt')
nltk.download('stopwords')
from nltk.corpus import stopwords
set(stopwords.words('english'))

"""**Loading the dataset from drive**"""

drive.mount('/content/drive')
filename_corpus = 'drive/MyDrive/Distro/corpus.txt'
filename_labels = 'drive/MyDrive/Distro/labels.txt'

#Loading the corpus
with open(filename_corpus) as f:
    corpus = f.readlines()

#Loading the labels (just to assess the quality of clustering)
with open(filename_labels) as f:
    labels = f.readlines()
labels = list(map(int, labels))

print("Corpus loaded into a list.")
print("There are ", len(corpus), " documents, and ", len(labels), " labels.")
print("This is the first document:", corpus[0])

"""**Preprocessing function**

This function is used to preprocess the documents (both the sampled dataset and the original one. It removes punctuations, stop words, numbers, upper cases. Then it applies some stemming and lemmatization to reduce the vocabulary size and consider very similar terms as a single term.
"""

def preprocessing(doc):

  #Tokenizing
  tokens = nltk.word_tokenize(doc, language='english')

  #Removing spunctuations and upper cases 
  tokens=[token.lower() for token in tokens if token.isalpha()]

  #Removing stopwords in english
  stop_words_en = stopwords.words('english')
  tokens = [w for w in tokens if w not in stop_words_en]  

  #Removing stopwods in spanish (we noticed that there were docs in spanish)
  stop_words_spa = stopwords.words('spanish')
  tokens = [w for w in tokens if w not in stop_words_spa]  

  #Stemming (since most of the docs were in english, stemming and lemmatiz are done in english)
  stemmer = nltk.stem.snowball.SnowballStemmer('english')
  tokens = [stemmer.stem(w) for w in tokens] 

  #Lemmatizing 
  lemmatizer = WordNetLemmatizer() 
  tokens = [lemmatizer.lemmatize(w) for w in tokens] 

  text = ' '.join(tokens)

  return text


# Just printing an example
print(corpus[201607])
print(preprocessing(corpus[201607]))
print("\n\n",corpus[0])
print(preprocessing(corpus[0]))

"""**Evaluation function**

This function just prints some metrics that are useful for the evaluation of clusters. We print all the metrics for completeness but we mostly focus on accuracy metric (since we have the true labels to compare).
"""

# Commented out IPython magic to ensure Python compatibility.
def evaluate(model, X, labels):
  print("Accuracy: %0.3f" %metrics.accuracy_score(labels, model.labels_))
  print("Homogeneity: %0.3f" % metrics.homogeneity_score(labels, model.labels_))
  print("Completeness: %0.3f" % metrics.completeness_score(labels, model.labels_))
  print("V-measure: %0.3f" % metrics.v_measure_score(labels, model.labels_))
  print("Adjusted Rand-Index: %.3f"
#       % metrics.adjusted_rand_score(labels, model.labels_))
  print("Silhouette Coefficient: %0.3f"
#       % metrics.silhouette_score(X, model.labels_, sample_size=1000))

def get_relevant_terms(model,vectorizer,n):
  centroids = model.cluster_centers_.argsort()[:, ::-1] ## Indices of largest centroids' entries in descending order
  terms = vectorizer.get_feature_names()
  for i in range(2):
    print("Cluster %d:" % i, end='')
    for ind in centroids[i, :n]:
      print(' %s' % terms[ind], end='')
    print()

"""The .argsort()[:, ::-1] line converts each centroid into a sorted (descending) list of the columns most "relevant" (highly-valued) in it, and hence the words most relevant (since words=columns).

**Wordcount function**

This function uses the information contained in the centroids to create a dictionary (key=term, value=tfidf) that is used as input to the WordCount implementation of matplotlib, to plot the most relevant words for each cluster. This kind of visualization helps to guess what are the main topics of the clusters.
"""

def plot_wordcount(centroids,vec):

  #Creating the dictionary that must be given as input to wordcount 
  #using the info provided by centroids (term indices and tfidf)
  word_freq = dict()
  centroids_indices = centroids.argsort()[:, ::-1] ## Indices of largest centroids' entries in descending order
  terms = vec.get_feature_names()
  for i in range(2):
    word_freq[i]={}
    for ind in centroids_indices[i]:
      word_freq[i][terms[ind]] = centroids[i][ind]
  
  #Plotting the words using wordcount
  for i in range(2):
    wordcloud = WordCloud(background_color="white", max_words=200, 
                          width=800, height=500).generate_from_frequencies(word_freq[i])
    plt.figure(figsize=(10,10))
    title = "Cluster " + str(i)
    plt.title(title)
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.show()

"""## Preprocessing and vectorizing the whole collection of docs"""

preprocessed = []
time_start = time.time()
for doc in corpus:
  preprocessed.append(preprocessing(doc))
time_end = time.time()
print("Corpus preprocessed in ", time_end-time_start, " seconds.")
print("Here's an example: ", preprocessed[0])

start_time = time.time()
#vec = HashingVectorizer()
vec = TfidfVectorizer(min_df=10) 
#vec = TfidfVectorizer() 
#we consider a term in the vocabulary only if it appears in at least 10 docs,
#otherwise we discard it
X = vec.fit_transform(preprocessed)
end_time = time.time()
print("\n", X.shape[0], " documents vectorized, ", X.shape[1], " features extracted in ", end_time-start_time, " seconds.")
print("Here's an example: ", X[0])
#X[0] is a sparse array, so it is printed in the format (row_index, col_index) value, where value is the hash of term frequency

"""## Clustering using Standard KMeans

This was done just to have an idea of the real time needed to Kmeans to cluster the entire dataset without any performance improving technique (sampling, dimensionality reduction, minibatch Kmeans...)

**Running Kmeans**
"""

print("Running KMeans . . .")
km = KMeans(init='k-means++', n_clusters=2)
t0 = time.time()
km.fit(X)
t_kmeans = time.time() - t0
print("KMeans ended in ", t_kmeans, " seconds.") #about 47 minutes

db1_labels = km.labels_
lab, counts = np.unique(db1_labels[db1_labels>=0], return_counts=True)
for i in range(km.n_clusters):
  print("|Cluster ",lab[i], "|: ", counts[i] )

"""**Evaluating results**"""

evaluate(km,X,labels) #the algorithm has just inverted the group labels

"""**Finding most relevant terms in clusters**"""

get_relevant_terms(km,vec,20)

"""## Clustering using Sampling and Dimensionality Reduction

**Random Sampling on the dataset:**

PROS: we avoid to preprocess each document (significantly speeding up the computation).

CONS: since it's random, we can not really be sure that the sampled dataset is representative enough for the population.
"""

sample_size = 31480 #we keep about 10% of the dataset
sample_set = []
sample_labels = []
print("Sampling. . .")
indices = list(range(0, len(corpus)))
random.shuffle(indices)
sampled_indices = random.sample(indices, sample_size)
for index in sampled_indices:
  sample_set.append(corpus[index])
  sample_labels.append(labels[index])
print("Sample size: ", len(sample_set))
print("Labels size: ", len(sample_labels))

print("Just an example: ", sample_set[0])

"""Preprocessing the sample set (much faster than the original corpus)"""

time_start = time.time()
for index,doc in enumerate(sample_set):
  sample_set[index] = preprocessing(doc)
time_end = time.time()
print("Corpus preprocessed in ", time_end-time_start, " seconds.")
print("Here's an example: ", sample_set[0])

#vec = HashingVectorizer()
start_time = time.time()
sample_vec = TfidfVectorizer()
Z = sample_vec.fit_transform(sample_set)
end_time = time.time()
print("\n", Z.shape[0], " documents vectorized, ", Z.shape[1], " features extracted in ", end_time-start_time, " seconds.")
print("Here's an example: ", Z[0])

"""We can try to use PCA to reduce the dimensionality, since the sampled data is much smaller than the original one. PCA requires the matrix in a dense representation, so we have to convert the sparse matrix using `toarray()`. Actually, this operation is not feasible even with the sampled dataset, because it causes the memory to explode..."""

pca = decomposition.PCA(n_components=2)
#This operation causes a crash due to memory exceed
Z_pca = Z.toarray()
pca.fit(Z_pca)
Z_pca = pca.transform(Z_pca)
pca.explained_variance_ratio_

"""Therefore, the best solution is to apply TruncatedSVD, that supports large sparse memory and does not require an explicit centering of the data. TruncatedSVD is the new version of the deprecated RandomizedPCA."""

k = 8
print("Decomposing the corpus with SVD. . .")
t0 = time.time()
svd = TruncatedSVD(k)
normalizer = Normalizer(copy=False)
lsa = make_pipeline(svd, normalizer)
Y = lsa.fit_transform(Z)
print("Decomposition ended in %f seconds" % (time.time() - t0))
print(svd.explained_variance_ratio_)

"""Running standard Kmeans on the sample set"""

print("Running KMeans . . .")
skm = KMeans(init='k-means++', n_clusters=2, max_iter=10000)
t0 = time.time()
skm.fit(Y)
st_kmeans = time.time() - t0
print("KMeans ended in ", st_kmeans, " seconds.")

db1_labels = skm.labels_
lab, counts = np.unique(db1_labels[db1_labels>=0], return_counts=True)
for i in range(skm.n_clusters):
  print("|Cluster ",lab[i], "|: ", counts[i] )

evaluate(skm,Y,sample_labels)

terms = sample_vec.get_feature_names()
print("Centroid shape in SVD: ", skm.cluster_centers_.shape) #in the reducted space we have just 2 dimensions and 2 centroids
original_centroids = svd.inverse_transform(skm.cluster_centers_)
print("Centroid shape in the original space: ", original_centroids.shape) #2 centroids and 64421 dimensions (features)
for i in range(original_centroids.shape[0]):
  original_centroids[i] = np.array([x for x in original_centroids[i]])
svd_centroids = original_centroids.argsort()[:, ::-1]

for i in range(2):
  print("Cluster %d:" % i, end='')
  for ind in svd_centroids[i, :20]:
    print(' %s' % terms[ind], end='')
  print()

plot_wordcount(original_centroids, sample_vec)

"""## Clustering using MiniBatchKmeans

Minibatch Kmeans clustering results really depend also on the random state, so you can have quite different results and accuracies running the algorithm different times. We found a good model with random_state=123456 and batch_size=10000.
"""

batch_sizes = [500, 1000, 5000, 10000]
acc = []
times = []
models = []
for batch in batch_sizes:
  print("\nRunning MiniBatchKMeans(batch size:", batch,") . . .")
  mbk = MiniBatchKMeans(init='k-means++', n_clusters=2, batch_size=batch, random_state=123456, 
                        max_iter=10000, max_no_improvement=20)
  t0 = time.time()
  mbk.fit(X)
  t_mini_batch = time.time() - t0
  print("KMeans ended in ", t_mini_batch, " seconds.\n")

  evaluate(mbk,X,labels)
  accuracy = metrics.accuracy_score(labels, mbk.labels_)
  if accuracy < 0.5 :
    acc.append(1-accuracy)
    #because it's just reversing cluster ids but clusters are correct
  else:
    acc.append(accuracy)
  times.append(t_mini_batch)
  models.append(mbk)
  print("--------------------------------------")

# Plot the points using matplotlib
plt.plot(batch_sizes, times)
plt.xticks(batch_sizes)
plt.xlabel("Batch size")
plt.ylabel("Computational Time (sec)")
plt.show()
plt.plot(batch_sizes, acc)
plt.xticks(batch_sizes)
plt.xlabel("Batch size")
plt.ylabel("Accuracy")
plt.show()

evaluate(mbk,X,labels)
#Notice that sometimes the accuracy goes to 0.1, 0.2 and so on.. 
# this means just that the Kmeans is considering cluster 1 as cluster 0 and
# cluster 0 as cluster 1, but that's not a big deal, because it is not a 
# classification task, we just want that our docs are separated in the correct
# groups, no matter what is the group "name"

print("\n")
db1_labels = mbk.labels_
lab, counts = np.unique(db1_labels[db1_labels>=0], return_counts=True)
for i in range(mbk.n_clusters):
  print("|Cluster ",lab[i], "|: ", counts[i] )

get_relevant_terms(mbk,vec,20)

"""## Clustering using Dimensionality Reduction

In practice TruncatedSVD is useful on large sparse datasets which cannot be centered without making the memory usage explode. PCA is mathematically defined as centering the data (removing the mean value to each feature) and then applying truncated SVD on the centered data.

As centering the data would destroy the sparsity and force a dense representation that does not fit in memory, we use directly truncated SVD on the sparse matrix (without centering). This resembles PCA but it's not exactly the same.
"""

k = 3
print("Decomposing the corpus with SVD. . .")
t0 = time.time()
svd = TruncatedSVD(k)
normalizer = Normalizer(copy=False)
lsa = make_pipeline(svd, normalizer)
Y = lsa.fit_transform(X)
print("Decomposition ended in %f seconds" % (time.time() - t0))
print(svd.explained_variance_ratio_)

print("Running KMeans . . .")
km = KMeans(init='k-means++', n_clusters=2, max_iter=1000000, n_init=10)
t0 = time.time()
km.fit(Y)
t_kmeans = time.time() - t0
print("KMeans ended in ", t_kmeans, " seconds.")

db1_labels = km.labels_
lab, counts = np.unique(db1_labels[db1_labels>=0], return_counts=True)
for i in range(km.n_clusters):
  print("|Cluster ",lab[i], "|: ", counts[i] )

evaluate(km,Y,labels)

terms = vec.get_feature_names()
print("Centroid shape in SVD: ", km.cluster_centers_.shape) #in the reducted space we have just 2 dimensions and 2 centroids
original_centroids = svd.inverse_transform(km.cluster_centers_)
print("Centroid shape in the original space: ", original_centroids.shape) #2 centroids and 64421 dimensions (features)
for i in range(original_centroids.shape[0]):
  original_centroids[i] = np.array([x for x in original_centroids[i]])
svd_centroids = original_centroids.argsort()[:, ::-1]

for i in range(2):
  print("Cluster %d:" % i, end='')
  for ind in svd_centroids[i, :20]:
    print(' %s' % terms[ind], end='')
  print()

centers = km.cluster_centers_
LABEL_COLOR_MAP = {0 : 'g',
                   1 : 'y',
                   3 : 'r',
                   }

label_color = [LABEL_COLOR_MAP[l] for l in km.labels_]

fig = plt.figure(1, figsize=(4, 4))
ax = Axes3D(fig, rect=[0, 0, .95, 1], elev=48, azim=134)
scatter = ax.scatter(Y[:, 0], Y[:, 1], Y[:, 2], c=label_color)
plt.title("Plotting PREDICTED clusters in Truncated SVD space")
plt.show()


label_color = [LABEL_COLOR_MAP[l] for l in labels]
centers = km.cluster_centers_
fig = plt.figure(1, figsize=(4, 4))
ax = Axes3D(fig, rect=[0, 0, .95, 1], elev=48, azim=134)
scatter = ax.scatter(Y[:, 0], Y[:, 1], Y[:, 2], c=label_color)
plt.title("Plotting REAL clusters in Truncated SVD space")
plt.show()


labs = []

for i in range(len(km.labels_)):
  if km.labels_[i] != labels[i]:
    labs.append(3)
  else:
    labs.append(labels[i])

label_color = [LABEL_COLOR_MAP[l] for l in labs]
centers = km.cluster_centers_
fig = plt.figure(1, figsize=(4, 4))
ax = Axes3D(fig, rect=[0, 0, .95, 1], elev=48, azim=134)
scatter = ax.scatter(Y[:, 0], Y[:, 1], Y[:, 2], c=label_color)
plt.title("Comparing real and predicted clusters in Truncated SVD space")
plt.show()

"""## Visualizing most relevant terms in each cluster (using best model)

Considering the metrics (mostly accuracy), our best model has the following characteristics:
*   Complete preprocessing (both stemming and lemmatization)
*   Tfidf vectorizer, min_df=10
*   MiniBatch Kmeans algorithm with random_state=123456 and batch_size = 10000,

reaching an accuracy of 0.913.


"""

best_model_centroids = mbk.cluster_centers_
best_model_vec = vec
plot_wordcount(best_model_centroids,best_model_vec)

"""Inspecting the visualization, we can guess the topics of the two clusters. Our corpus seems to be about products reviews.The **first cluster** regards a product for **babies**, and this is proved by the presence of terms like `babi` (that is also the mostrelevant word of the cluster), but also `daughter`,`diaper`,`kid`,`child`. We can guess that we are talking about a product (`use`,`product`,`bought`,`buy`,`item`) that seems to be mostly recommended (`love`,`recommend`,`great`,`like`,`good`,`perfect`,`well`,`nice`,`comfort`,`super`); we can not be sure that each of these words was referred to the product itself in the reviews, but the presence ofonly positive terms in the word cloud should at least reflect a general positive feeling about the product.

The **second cluster** is about reviews of a product for dogs or cats (`dog`,`cat`,`kitten`, `puppi`,`pet`).  Again, it is not clear what kind of product (or products) it is, but it may be related to some food(`eat`,`flavor`,`smell`,`chew`,`bowl`,`teeth`) or to a `toy`(maybe a `ball`?) for pets. The terms `help`,`treat` and `problem` may suggest that the product is used (`use`,`give`) to treat some problematic behaviour in pets, probably related to eating and food. The general feeling about the product seems to be positive (`love`,`like`,`great`,`well`).
"""