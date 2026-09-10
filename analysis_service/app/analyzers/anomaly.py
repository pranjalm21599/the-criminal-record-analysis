from app.neo4j_driver import db


def detect_transaction_anomalies(threshold=100000):
    query = """
    MATCH (a:BankAccount)-[r:TRANSFERRED_TO]->(b:BankAccount)
    WHERE r.amount >= $threshold
    RETURN
        a.account_number AS from_account,
        b.account_number AS to_account,
        r.amount AS amount,
        r.date AS date
    ORDER BY r.amount DESC
    """

    records = db.execute_query(
        query,
        {"threshold": threshold}
    )

    return {
        "threshold": threshold,
        "total_anomalies": len(records),
        "anomalies": records
    }


def detect_call_anomalies():
    query = """
    MATCH (p1:Phone)-[r:CALLED]->(p2:Phone)
    WHERE r.call_count >= 10 OR r.total_duration >= 1000
    RETURN
        p1.number AS from_phone,
        p2.number AS to_phone,
        r.call_count AS call_count,
        r.total_duration AS total_duration,
        NULL AS date
    ORDER BY r.call_count DESC
    """

    records = db.execute_query(query)

    return {
        "total_anomalies": len(records),
        "anomalies": records
    }
import pandas as pd
from sklearn.ensemble import IsolationForest


def detect_ml_anomalies():
    query = """
    MATCH (p1:Phone)-[r:CALLED]->(p2:Phone)
    RETURN
        p1.number AS from_phone,
        p2.number AS to_phone,
        r.call_count AS call_count,
        r.total_duration AS total_duration
    """

    records = db.execute_query(query)

    if len(records) < 2:
        return {
            "total_anomalies": 0,
            "anomalies": []
        }

    df = pd.DataFrame(records)

    features = df[
        ["call_count", "total_duration"]
    ]

    model = IsolationForest(
        contamination="auto",
        random_state=42
    )

    df["prediction"] = model.fit_predict(features)

    anomalies = df[
        df["prediction"] == -1
    ].drop(columns=["prediction"])

    return {
        "total_anomalies": len(anomalies),
        "anomalies": anomalies.to_dict(orient="records")
    }
