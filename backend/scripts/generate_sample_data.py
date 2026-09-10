import pandas as pd
import random
from datetime import datetime, timedelta

def generate_synthetic_data():
    # 1. Create Cases
    cases = []
    for i in range(1, 21):
        cases.append({
            "case_number": f"CASE-2026-{i:03d}",
            "title": f"Organized Crime Operation {chr(64+i)}",
            "status": "Under Investigation"
        })
    pd.DataFrame(cases).to_csv("sample_data/cases.csv", index=False)

    # 2. Create Persons (with a "Kingpin" pattern)
    persons = []
    for i in range(1, 101):
        is_kingpin = (i == 1)
        persons.append({
            "name": f"Subject {i}" if not is_kingpin else "Main Target Alpha",
            "role": "Suspect" if i < 50 else "Associate",
            "phone_numbers": f"98765{i:05d}"
        })
    pd.DataFrame(persons).to_csv("sample_data/persons.csv", index=False)

    # 3. Create CDR (Call Detail Records) - Creating a Cluster
    cdrs = []
    # Cluster: Everyone calls the Kingpin (9876500001)
    for i in range(2, 20):
        for _ in range(5): # 5 calls each
            cdrs.append({
                "caller_number": f"98765{i:05d}",
                "receiver_number": "9876500001",
                "duration": random.randint(30, 300),
                "timestamp": datetime.now() - timedelta(days=random.randint(0, 30))
            })
    pd.DataFrame(cdrs).to_csv("sample_data/call_records.csv", index=False)
    print("Synthetic data generated in sample_data/ folder.")

if __name__ == "__main__":
    generate_synthetic_data()