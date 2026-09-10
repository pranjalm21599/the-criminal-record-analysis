from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from ..database import Base

class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    aliases = Column(String) # Comma separated
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String)
    nationality = Column(String, default="Indian")
    phone_numbers = Column(String) # JSON or comma-separated
    addresses = Column(Text)
    role = Column(String) # Suspect, Witness, Victim
    criminal_history = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())