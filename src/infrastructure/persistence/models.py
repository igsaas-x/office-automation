from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone

Base = declarative_base()


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

class GroupModel(Base):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True)
    chat_id = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utc_now)

    check_ins = relationship('CheckInModel', back_populates='group')
    employee_groups = relationship('EmployeeGroupModel', back_populates='group')

class EmployeeModel(Base):
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utc_now)

    check_ins = relationship('CheckInModel', back_populates='employee')
    salary_advances = relationship('SalaryAdvanceModel', back_populates='employee')
    employee_groups = relationship('EmployeeGroupModel', back_populates='employee')

class EmployeeGroupModel(Base):
    __tablename__ = 'employee_groups'

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    joined_at = Column(DateTime, default=utc_now)

    employee = relationship('EmployeeModel', back_populates='employee_groups')
    group = relationship('GroupModel', back_populates='employee_groups')

    __table_args__ = (
        UniqueConstraint('employee_id', 'group_id', name='uq_employee_group'),
    )

class CheckInModel(Base):
    __tablename__ = 'check_ins'

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    photo_url = Column(String(512), nullable=True)
    timestamp = Column(DateTime, default=utc_now)

    employee = relationship('EmployeeModel', back_populates='check_ins')
    group = relationship('GroupModel', back_populates='check_ins')

class SalaryAdvanceModel(Base):
    __tablename__ = 'salary_advances'

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'))
    amount = Column(String(50), nullable=False)  # Store as string to preserve precision
    note = Column(Text)
    created_by = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=utc_now)

    employee = relationship('EmployeeModel', back_populates='salary_advances')
