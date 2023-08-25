# preprocessing/stopword_removal.py

from nltk.corpus import stopwords


def remove_stopwords(tokens):
    stop_words = set(stopwords.words("english"))
    return [token for token in tokens if token not in stop_words]
