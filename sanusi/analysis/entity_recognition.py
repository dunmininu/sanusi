from functools import lru_cache

def extract_keywords(text):
    from rake_nltk import Rake

    r = Rake()
    r.extract_keywords_from_text(text)
    return r.get_ranked_phrases()


@lru_cache(maxsize=1)
def get_nlp():
    import spacy
    return spacy.load("en_core_web_sm")


def extract_entities(text):
    nlp = get_nlp()
    doc = nlp(text)
    return [(ent.text, ent.label_) for ent in doc.ents]


def extract_topics(text):
    keywords = extract_keywords(text)
    entities = [ent[0] for ent in extract_entities(text)]

    combined = list(set(keywords + entities))

    return {
        "keywords": list(set(keywords)), # To ensure no duplicate keywords
        "entities": list(set(entities)), # To ensure no duplicate entities
        "combined": combined,
    }

