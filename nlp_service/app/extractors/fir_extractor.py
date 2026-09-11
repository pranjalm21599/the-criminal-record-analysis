import re

from app.extractors.ner_extractor import NERExtractor
from app.extractors.pattern_extractor import PatternExtractor


class FIRExtractor:

    def __init__(self):

        self.ner = NERExtractor()
        self.patterns = PatternExtractor()

    def extract_fir_header(self, text):

        result = {}

        # Extract FIR number
        fir_match = re.search(
            r"(?:FIR|F\.I\.R\.?|First Information Report)"
            r"\s*(?:No\.?|Number)?\s*:?\s*(\d+/\d+|\d+)",
            text,
            re.IGNORECASE
        )

        result["fir_number"] = (
            fir_match.group(1)
            if fir_match
            else None
        )

        # Extract police station
        ps_match = re.search(
            r"(?:Police Station|P\.S\.)"
            r"\s*:?\s*([A-Za-z\s]+?)(?:\n|,|district)",
            text,
            re.IGNORECASE
        )

        result["police_station"] = (
            ps_match.group(1).strip()
            if ps_match
            else None
        )

        # Extract IPC sections
        result["ipc_sections"] = (
            self.ner.extract_ipc_sections(text)
        )

        return result

    def extract_full_fir(self, text, fir_id):

        # NLP entities
        ner_entities = self.ner.extract_entities(text)

        # Regex entities
        pattern_entities = self.patterns.extract_all(text)

        # FIR header
        header = self.extract_fir_header(text)

        # Crime keywords
        crimes = self.ner.extract_crime_events(text)

        # Relationships
        relationships = self.ner.extract_relationships(text)

        return {
            "fir_id": fir_id,

            "header": header,

            "persons": ner_entities.get(
                "persons", []
            ),

            "locations": ner_entities.get(
                "locations", []
            ),

            "organizations": ner_entities.get(
                "organizations", []
            ),

            "dates": ner_entities.get(
                "dates", []
            ),

            "phones": pattern_entities.get(
                "phone", []
            ),

            "vehicles": pattern_entities.get(
                "vehicle", []
            ),

            "aadhaar_numbers": pattern_entities.get(
                "aadhaar", []
            ),

            "pan_numbers": pattern_entities.get(
                "pan", []
            ),

            "bank_accounts": pattern_entities.get(
                "bank_account", []
            ),

            "amounts": pattern_entities.get(
                "amount", []
            ),

            "ipc_sections": header.get(
                "ipc_sections", []
            ),

            "crimes_mentioned": crimes,

            "relationships": relationships
        }


if __name__ == "__main__":

    extractor = FIRExtractor()

    text = """
    FIR No. 123/2026
    Police Station: Delhi

    Ravi Kumar was arrested in Delhi for robbery.
    His phone number is 9876543210.
    Vehicle number is DL 01 AB 1234.
    PAN ABCDE1234F.
    The incident occurred on 15 March 2026.
    IPC Section 394 was applied.
    """

    result = extractor.extract_full_fir(
        text,
        123
    )

    print(result)