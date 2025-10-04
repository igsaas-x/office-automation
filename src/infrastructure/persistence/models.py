from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class EmployeeModel(Base):
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    check_ins = relationship('CheckInModel', back_populates='employee')
    salary_advances = relationship('SalaryAdvanceModel', back_populates='employee')

class CheckInModel(Base):
    __tablename__ = 'check_ins'

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    employee = relationship('EmployeeModel', back_populates='check_ins')

class SalaryAdvanceModel(Base):
    __tablename__ = 'salary_advances'

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'))
    amount = Column(String, nullable=False)  # Store as string to preserve precision
    note = Column(Text)
    created_by = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    employee = relationship('EmployeeModel', back_populates='salary_advances')
