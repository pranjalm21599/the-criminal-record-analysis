import spacy

nlp = spacy.load("en_core_web_sm")

text = "Rahul Sharma met with Amit Kumar in Delhi on 10 September 2026. They traveled in a Toyota car."

doc = nlp(text)

for entity in doc.ents:
    print(entity.text, "->", entity.label_)