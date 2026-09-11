"""
Relational schema for the structured evidence: cases, FIRs, call detail
records, financial transactions, and the entities NLP pulls out of them.
"""
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(64), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    status = Column(String(32), default="open", index=True)
    created_at = Column(DateTime, default=_utcnow)

    firs = relationship("FIR", back_populates="case", cascade="all, delete-orphan")
    call_records = relationship("CallRecord", back_populates="case", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="case", cascade="all, delete-orphan")


class FIR(Base):
    __tablename__ = "firs"

    id = Column(Integer, primary_key=True, index=True)
    fir_number = Column(String(64), index=True, nullable=False)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True, index=True)
    police_station = Column(String(128), default="")
    offense_type = Column(String(128), default="")
    date_filed = Column(String(32), default="")
    raw_text = Column(Text, default="")
    source_file = Column(String(255), default="")
    created_at = Column(DateTime, default=_utcnow)

    case = relationship("Case", back_populates="firs")


class CallRecord(Base):
    __tablename__ = "call_records"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True, index=True)
    caller = Column(String(32), index=True, nullable=False)
    receiver = Column(String(32), index=True, nullable=False)
    duration = Column(Integer, default=0)
    call_time = Column(String(64), default="")
    tower_location = Column(String(255), default="")
    created_at = Column(DateTime, default=_utcnow)

    case = relationship("Case", back_populates="call_records")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True, index=True)
    from_account = Column(String(64), index=True, nullable=False)
    to_account = Column(String(64), index=True, nullable=False)
    amount = Column(Float, default=0.0)
    txn_date = Column(String(64), default="")
    memo = Column(String(255), default="")
    created_at = Column(DateTime, default=_utcnow)

    case = relationship("Case", back_populates="transactions")


class ExtractedEntity(Base):
    """One entity NLP found in a document — the handoff record to the graph."""

    __tablename__ = "extracted_entities"

    id = Column(Integer, primary_key=True, index=True)
    fir_id = Column(Integer, ForeignKey("firs.id"), nullable=True, index=True)
    entity_type = Column(String(32), index=True)  # person / phone / vehicle / location ...
    value = Column(String(255), index=True)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=_utcnow)
