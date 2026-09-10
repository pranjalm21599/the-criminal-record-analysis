import re

class DataNormalizer:
    @staticmethod
    def normalize_phone(phone: str) -> str:
        # Remove all non-numeric chars
        digits = re.sub(r'\D', '', str(phone))
        # Take last 10 digits for Indian context
        return digits[-10:] if len(digits) >= 10 else digits

    @staticmethod
    def normalize_name(name: str) -> str:
        if not name: return ""
        return name.strip().upper()

    @staticmethod
    def clean_monetary(value: any) -> float:
        try:
            if isinstance(value, str):
                value = value.replace(',', '').replace('₹', '').strip()
            return float(value)
        except:
            return 0.0