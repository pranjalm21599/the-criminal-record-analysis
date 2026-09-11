"""
Anomaly detection over financial transactions and call records.

Two layers, deliberately:

1. Rule flags an investigator can defend in court ("just under the ₹10 lakh
   reporting threshold", "3am transfer", "rapid pass-through").
2. IsolationForest over engineered features, to catch the odd-shaped records
   the rules don't describe.

The rules matter as much as the model here — "the AI said so" is not evidence,
but "this transfer is ₹9.9 lakh, structured just below the reporting limit" is.
"""
import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, List

import numpy as np
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)

# India's cash transaction reporting threshold. Amounts that sit just below it
# are the classic structuring signal.
REPORTING_THRESHOLD = 1_000_000
STRUCTURING_BAND = 0.9  # 90-100% of the threshold


def _parse_hour(value: str) -> int:
    """Pull an hour-of-day out of the many timestamp formats CSVs arrive in."""
    if not value:
        return -1
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value.strip(), fmt).hour
        except ValueError:
            continue
    # Bare "HH:MM" or a timestamp we couldn't fully parse
    parts = value.strip().split()
    for part in parts:
        if ":" in part:
            try:
                return int(part.split(":")[0])
            except ValueError:
                pass
    return -1


def detect_transaction_anomalies(transactions: List[Dict]) -> List[Dict]:
    if not transactions:
        return []

    # How much each account sends and receives — used for pass-through detection.
    sent = defaultdict(float)
    received = defaultdict(float)
    for txn in transactions:
        sent[txn.get("from_account", "")] += float(txn.get("amount") or 0)
        received[txn.get("to_account", "")] += float(txn.get("amount") or 0)

    amounts = np.array([float(t.get("amount") or 0) for t in transactions], dtype=float)
    mean_amount = float(amounts.mean()) if amounts.size else 0.0
    std_amount = float(amounts.std()) if amounts.size else 0.0

    features = []
    for txn in transactions:
        amount = float(txn.get("amount") or 0)
        hour = _parse_hour(str(txn.get("date", "")))
        features.append([
            amount,
            hour if hour >= 0 else 12,
            sent[txn.get("from_account", "")],
            received[txn.get("to_account", "")],
        ])

    ml_flags = _isolation_forest_flags(np.array(features, dtype=float))

    results = []
    for index, txn in enumerate(transactions):
        amount = float(txn.get("amount") or 0)
        hour = _parse_hour(str(txn.get("date", "")))
        flags: List[str] = []

        if REPORTING_THRESHOLD * STRUCTURING_BAND <= amount < REPORTING_THRESHOLD:
            flags.append("STRUCTURING_BELOW_THRESHOLD")
        if amount >= REPORTING_THRESHOLD:
            flags.append("LARGE_VALUE")
        if std_amount > 0 and amount > mean_amount + 2 * std_amount:
            flags.append("STATISTICAL_OUTLIER")
        if 0 <= hour <= 5:
            flags.append("ODD_HOUR_TRANSFER")

        # A mule account: money lands and leaves almost untouched.
        from_account = txn.get("from_account", "")
        if received[from_account] > 0:
            pass_through = sent[from_account] / received[from_account]
            if 0.9 <= pass_through <= 1.1 and sent[from_account] > 0:
                flags.append("PASS_THROUGH_ACCOUNT")

        if ml_flags[index]:
            flags.append("ML_ANOMALY")

        if flags:
            results.append({
                "transaction_id": txn.get("id"),
                "from_account": from_account,
                "to_account": txn.get("to_account", ""),
                "amount": amount,
                "date": txn.get("date", ""),
                "flags": flags,
                "severity": "HIGH" if len(flags) >= 2 else "MEDIUM",
            })

    results.sort(key=lambda r: (len(r["flags"]), r["amount"]), reverse=True)
    return results


def _isolation_forest_flags(features: np.ndarray) -> List[bool]:
    """
    Returns a per-row 'is anomalous' flag. IsolationForest needs a handful of
    samples to say anything meaningful, so below that we simply flag nothing
    rather than emitting noise.
    """
    if features.size == 0 or len(features) < 8:
        return [False] * len(features)

    try:
        model = IsolationForest(contamination=0.1, random_state=42, n_estimators=100)
        predictions = model.fit_predict(features)
        return [bool(p == -1) for p in predictions]
    except Exception as exc:
        logger.warning("IsolationForest failed: %s", exc)
        return [False] * len(features)


def detect_call_anomalies(call_records: List[Dict]) -> List[Dict]:
    if not call_records:
        return []

    pair_stats: Dict[tuple, Dict] = defaultdict(
        lambda: {"count": 0, "total_duration": 0, "odd_hour": 0, "very_short": 0}
    )
    caller_contacts = defaultdict(set)

    for record in call_records:
        caller = str(record.get("caller", ""))
        receiver = str(record.get("receiver", ""))
        if not caller or not receiver:
            continue

        duration = int(record.get("duration") or 0)
        hour = _parse_hour(str(record.get("call_time", "")))

        stats = pair_stats[(caller, receiver)]
        stats["count"] += 1
        stats["total_duration"] += duration
        if 0 <= hour <= 5:
            stats["odd_hour"] += 1
        if 0 < duration <= 10:
            stats["very_short"] += 1

        caller_contacts[caller].add(receiver)

    counts = [s["count"] for s in pair_stats.values()]
    mean_count = float(np.mean(counts)) if counts else 0.0
    std_count = float(np.std(counts)) if counts else 0.0
    burst_threshold = max(mean_count + 2 * std_count, 5)

    anomalies = []
    for (caller, receiver), stats in pair_stats.items():
        flags = []
        if stats["count"] >= burst_threshold:
            flags.append("HIGH_FREQUENCY")
        if stats["odd_hour"] >= 3:
            flags.append("ODD_HOUR_PATTERN")
        # Many very short calls between one pair reads as coded signalling.
        if stats["very_short"] >= 3 and stats["very_short"] / stats["count"] > 0.5:
            flags.append("BURST_SHORT_CALLS")
        if len(caller_contacts[caller]) >= 10:
            flags.append("HUB_NUMBER")

        if flags:
            anomalies.append({
                "caller": caller,
                "receiver": receiver,
                "call_count": stats["count"],
                "total_duration": stats["total_duration"],
                "flags": flags,
                "severity": "HIGH" if len(flags) >= 2 else "MEDIUM",
                "description": (
                    f"{caller} → {receiver}: {stats['count']} calls "
                    f"({', '.join(flags)})"
                ),
            })

    anomalies.sort(key=lambda a: (len(a["flags"]), a["call_count"]), reverse=True)
    return anomalies
