import pandas as pd


class CDRExtractor:

    def analyze_cdr(self, records):

        df = pd.DataFrame(records)

        results = {
            "phone_network": [],
            "frequent_contacts": {},
            "active_hours": {},
            "suspicious_patterns": []
        }

        if df.empty:
            return results

        # Analyze phone-to-phone connections
        if "caller_number" in df.columns and "receiver_number" in df.columns:

            grouped = df.groupby(
                ["caller_number", "receiver_number"]
            ).agg(
                call_count=("call_duration", "count"),
                total_duration=("call_duration", "sum")
            ).reset_index()

            for _, row in grouped.iterrows():

                results["phone_network"].append({
                    "from_phone": row["caller_number"],
                    "to_phone": row["receiver_number"],
                    "call_count": int(row["call_count"]),
                    "total_duration_seconds": int(
                        row["total_duration"]
                    )
                })

        # Find frequent contacts
        for caller, group in df.groupby("caller_number"):

            contacts = (
                group["receiver_number"]
                .value_counts()
                .to_dict()
            )

            results["frequent_contacts"][caller] = contacts

        # Analyze active calling hours
        if "timestamp" in df.columns:

            df["timestamp"] = pd.to_datetime(
                df["timestamp"],
                errors="coerce"
            )

            df["hour"] = df["timestamp"].dt.hour

            for hour, group in df.groupby("hour"):

                results["active_hours"][str(int(hour))] = int(
                    len(group)
                )

                # Flag late-night calls
                if hour >= 23 or hour < 5:

                    results["suspicious_patterns"].append({
                        "type": "late_night_activity",
                        "hour": int(hour),
                        "call_count": int(len(group))
                    })

        return results


if __name__ == "__main__":

    extractor = CDRExtractor()

    records = [
        {
            "caller_number": "9876543210",
            "receiver_number": "9123456789",
            "call_duration": 120,
            "timestamp": "2026-09-10 23:30:00"
        },
        {
            "caller_number": "9876543210",
            "receiver_number": "9123456789",
            "call_duration": 180,
            "timestamp": "2026-09-10 14:30:00"
        },
        {
            "caller_number": "9123456789",
            "receiver_number": "9876543210",
            "call_duration": 90,
            "timestamp": "2026-09-10 01:15:00"
        }
    ]

    result = extractor.analyze_cdr(records)

    print(result)