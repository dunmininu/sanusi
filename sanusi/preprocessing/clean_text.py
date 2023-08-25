import string


def lowercase_text(text):
    return text.lower()


def remove_punctuation(text):
    return text.translate(str.maketrans("", "", string.punctuation))
