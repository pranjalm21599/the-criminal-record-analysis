from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class FIR(Base):
    __tablename__ = "firs"

    id = Column(Integer, primary_key=True, index=True)
    fir_number = Column(String, unique=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    
    police_station = Column(String)
    district = Column(String)
    state = Column(String)
    date_filed = Column(DateTime)
    
    complainant_name = Column(String)
    accused_names = Column(Text) # Stored as comma-separated or JSON string
    offense_type = Column(String)
    ipc_sections = Column(String)
    description = Column(Text)
    
    location = Column(String)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    raw_text = Column(Text) # Crucial for Member 2 (NLP)
    source_file = Column(String)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    case = relationship("Case", back_populates="firs")