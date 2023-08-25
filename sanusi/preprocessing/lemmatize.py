# preprocessing/lemmatize.py

from nltk.stem import WordNetLemmatizer


def lemmatize_text(tokens):
    lemmatizer = WordNetLemmatizer()
    return [lemmatizer.lemmatize(token) for token in tokens]
