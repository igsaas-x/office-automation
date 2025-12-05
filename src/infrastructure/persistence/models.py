from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Date, ForeignKey, Text, UniqueConstraint
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


# Vehicle Logistics Models

class VehicleModel(Base):
    __tablename__ = 'vehicles'

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    license_plate = Column(String(20), nullable=False)
    vehicle_type = Column(String(20), nullable=False)  # TRUCK, VAN, MOTORCYCLE, CAR
    created_at = Column(DateTime, default=utc_now)

    group = relationship('GroupModel')
    drivers = relationship('DriverModel', back_populates='assigned_vehicle')
    trips = relationship('TripModel', back_populates='vehicle')
    fuel_records = relationship('FuelRecordModel', back_populates='vehicle')

    __table_args__ = (
        UniqueConstraint('group_id', 'license_plate', name='uq_group_license_plate'),
    )


class DriverModel(Base):
    __tablename__ = 'drivers'

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    role = Column(String(20), nullable=False, default='DRIVER')
    assigned_vehicle_id = Column(Integer, ForeignKey('vehicles.id'), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    group = relationship('GroupModel')
    assigned_vehicle = relationship('VehicleModel', back_populates='drivers')
    trips = relationship('TripModel', back_populates='driver')

    __table_args__ = (
        UniqueConstraint('group_id', 'phone', name='uq_group_phone'),
    )


class TripModel(Base):
    __tablename__ = 'trips'

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id'), nullable=False)
    driver_id = Column(Integer, ForeignKey('drivers.id'), nullable=False)
    date = Column(Date, nullable=False)
    trip_number = Column(Integer, nullable=False)  # Auto-increments daily per vehicle
    loading_size_cubic_meters = Column(Float, nullable=True)  # Loading size in cubic meters
    created_at = Column(DateTime, default=utc_now)

    group = relationship('GroupModel')
    vehicle = relationship('VehicleModel', back_populates='trips')
    driver = relationship('DriverModel', back_populates='trips')

    __table_args__ = (
        UniqueConstraint('vehicle_id', 'date', 'trip_number', name='uq_vehicle_date_trip_number'),
    )


class FuelRecordModel(Base):
    __tablename__ = 'fuel_records'

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id'), nullable=False)
    date = Column(Date, nullable=False)
    liters = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)
    receipt_photo_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    group = relationship('GroupModel')
    vehicle = relationship('VehicleModel', back_populates='fuel_records')
