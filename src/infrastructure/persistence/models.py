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
    business_name = Column(String(255), nullable=True)  # Business/branch name
    package_level = Column(String(20), nullable=False, default='free')  # free, basic, premium
    package_updated_at = Column(DateTime, nullable=True)  # When package was last updated
    package_updated_by = Column(String(255), nullable=True)  # Admin Telegram ID who updated
    created_at = Column(DateTime, default=utc_now)

    check_ins = relationship('CheckInModel', back_populates='group')
    employee_groups = relationship('EmployeeGroupModel', back_populates='group')

class EmployeeModel(Base):
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    role = Column(String(100), nullable=True)
    date_start_work = Column(DateTime, nullable=True)
    probation_months = Column(Integer, nullable=True)
    base_salary = Column(Float, nullable=True)
    bonus = Column(Float, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    check_ins = relationship('CheckInModel', back_populates='employee')
    salary_advances = relationship('SalaryAdvanceModel', back_populates='employee')
    employee_groups = relationship('EmployeeGroupModel', back_populates='employee')
    allowances = relationship('AllowanceModel', back_populates='employee')

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

class AllowanceModel(Base):
    __tablename__ = 'allowances'

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    amount = Column(Float, nullable=False)
    allowance_type = Column(String(100), nullable=False)  # e.g., 'transport', 'meal', 'housing', etc.
    note = Column(Text)
    created_by = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=utc_now)

    employee = relationship('EmployeeModel', back_populates='allowances')
