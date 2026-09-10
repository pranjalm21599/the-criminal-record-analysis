import spacy
import re


class NERExtractor:

    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

        self.crime_keywords = [
            "murder",
            "robbery",
            "theft",
            "assault",
            "kidnapping",
            "trafficking",
            "drug",
            "narcotics",
            "smuggling",
            "fraud",
            "extortion",
            "gang",
            "dacoity",
            "rape",
            "forgery"
        ]

    def extract_entities(self, text):

        doc = self.nlp(text)

        entities = {
            "persons": [],
            "locations": [],
            "organizations": [],
            "dates": [],
            "events": [],
            "misc": []
        }

        for ent in doc.ents:

            entity_data = {
                "text": ent.text.strip(),
                "start_char": ent.start_char,
                "end_char": ent.end_char,
                "label": ent.label_
            }

            if ent.label_ == "PERSON":
                entities["persons"].append(entity_data)

            elif ent.label_ in ["GPE", "LOC", "FAC"]:
                entities["locations"].append(entity_data)

            elif ent.label_ == "ORG":
                entities["organizations"].append(entity_data)

            elif ent.label_ in ["DATE", "TIME"]:
                entities["dates"].append(entity_data)

            elif ent.label_ == "EVENT":
                entities["events"].append(entity_data)

            else:
                entities["misc"].append(entity_data)

        return entities

    def extract_crime_events(self, text):

        text_lower = text.lower()

        found_crimes = []

        for crime in self.crime_keywords:

            if crime in text_lower:
                found_crimes.append(crime)

        return found_crimes

    def extract_ipc_sections(self, text):

        pattern = r'(?:IPC|section|sec\.?|u/s)\s*(\d+(?:[A-Z])?)'

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )

        return list(set(matches))

    def extract_relationships(self, text):

        doc = self.nlp(text)

        relationships = []

        relationship_keywords = {
            "accused": [
                "accused",
                "arrested",
                "charged",
                "nabbed"
            ],

            "victim": [
                "victim",
                "complainant",
                "injured"
            ],

            "witness": [
                "witness",
                "testified"
            ],

            "associated": [
                "associate",
                "partner",
                "accomplice"
            ]
        }

        persons = [
            ent for ent in doc.ents
            if ent.label_ == "PERSON"
        ]

        for person in persons:

            start = max(
                0,
                person.start_char - 50
            )

            end = min(
                len(text),
                person.end_char + 100
            )

            context = text[
                start:end
            ].lower()

            for role, keywords in relationship_keywords.items():

                for keyword in keywords:

                    if keyword in context:

                        relationships.append({
                            "person": person.text,
                            "role": role,
                            "context": text[
                                start:end
                            ].strip()
                        })

                        break

        return relationships
if __name__ == "__main__":

    extractor = NERExtractor()

    text = """
    Ravi Kumar was arrested in Mumbai for robbery.
    He was associated with Amit Sharma.
    The incident occurred on 15 March 2024.
    IPC Section 394 was applied.
    """

    print("ENTITIES:")
    print(extractor.extract_entities(text))

    print("\nCRIMES:")
    print(extractor.extract_crime_events(text))

    print("\nIPC:")
    print(extractor.extract_ipc_sections(text))

    print("\nRELATIONSHIPS:")
    print(extractor.extract_relationships(text))