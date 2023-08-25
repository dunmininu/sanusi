from preprocessing.clean_text import lowercase_text, remove_punctuation
from preprocessing.tokenize import tokenize_text
from preprocessing.stopword_removal import remove_stopwords
from preprocessing.lemmatize import lemmatize_text


def preprocess_text(text):
    text = lowercase_text(text)
    text = remove_punctuation(text)
    tokens = tokenize_text(text)
    tokens = remove_stopwords(tokens)
    tokens = lemmatize_text(tokens)

    return tokens
