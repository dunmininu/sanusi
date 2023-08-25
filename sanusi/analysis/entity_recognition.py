from rake_nltk import Rake
import spacy

nlp = spacy.load("en_core_web_sm")


def extract_keywords(text):
    r = Rake()
    r.extract_keywords_from_text(text)
    return r.get_ranked_phrases()


def extract_entities(text):
    doc = nlp(text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    return entities


def extract_topics(text):
    keywords = extract_keywords(text)
    entities = [ent[0] for ent in extract_entities(text)]

    # Combine and remove duplicates for combined topics (if needed in future)
    combined = list(set(keywords + entities))

    result = {
        "keywords": list(set(keywords)),  # To ensure no duplicate keywords
        "entities": list(set(entities)),  # To ensure no duplicate entities
    }

    return result
