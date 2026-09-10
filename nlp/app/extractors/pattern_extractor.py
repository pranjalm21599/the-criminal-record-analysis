import re


class PatternExtractor:

    def __init__(self):

        self.patterns = {

            "phone": [
                r"\b(?:\+91|91)?[-\s]?[6-9]\d{9}\b"
            ],

            "vehicle": [
                r"\b[A-Z]{2}[-\s]?\d{1,2}[-\s]?[A-Z]{1,2}[-\s]?\d{4}\b"
            ],

            "aadhaar": [
                r"\b[2-9]\d{3}[-\s]\d{4}[-\s]\d{4}\b",
                r"\b[2-9]\d{11}\b"
            ],

            "pan": [
                r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"
            ],

            "bank_account": [
                r"\b\d{12,18}\b"
            ],

            "ifsc": [
                r"\b[A-Z]{4}0[A-Z0-9]{6}\b"
            ],

            "email": [
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
            ],

            "amount": [
                r"(?:Rs\.?|₹|INR)\s*[\d,]+(?:\.\d{2})?"
            ],

            "date": [
                r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
                r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b"
            ]
        }

    def extract_all(self, text):

        results = {}

        for entity_type, patterns in self.patterns.items():

            found = set()

            for pattern in patterns:

                matches = re.findall(
                    pattern,
                    text,
                    re.IGNORECASE
                )
                for match in matches:
                    found.add(match.strip())

            results[entity_type] = list(found)

        return results


if __name__ == "__main__":

    extractor = PatternExtractor()

    text = """
    Ravi Kumar phone 9876543210.
    Vehicle MH 01 AB 1234.
    PAN ABCDE1234F.
    Aadhaar 2345 6789 0123.
    Email ravi@example.com.
    Amount ₹2,50,000.
    Date 15 March 2024.
    """

    result = extractor.extract_all(text)

    for key, value in result.items():
        print(key, ":", value)