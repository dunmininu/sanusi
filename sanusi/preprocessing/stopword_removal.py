# preprocessing/stopword_removal.py


def remove_stopwords(tokens):
    from nltk.corpus import stopwords

    stop_words = set(stopwords.words("english"))
    return [token for token in tokens if token not in stop_words]
