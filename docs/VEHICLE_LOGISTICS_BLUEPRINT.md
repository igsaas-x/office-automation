# Vehicle Logistics Tracking - Blueprint (Phase 1)

## Overview

Simple vehicle trip and fuel tracking system for logistics operations via Telegram bot.

---

## Core Requirements - Phase 1

### Setup
1. Register drivers (Name, Phone, Role)
2. Register vehicles (License plate/ស្លាកលេខឡាន, Type, Driver assignment)

### Daily Operations
1. Record trips - track how many trips each vehicle makes per day (auto-increment)
2. Record fuel refills (ចាក់ប្រេង - liters, cost, receipt photo)
3. Quick daily overview (/today)

### Reports
1. Daily report (របាយការថ្ងៃ) with export
2. Monthly report (របាយការខែ) with export
3. Vehicle performance analytics
4. Excel & PDF export

---

## 1. Database Entities

### Driver
```python
Driver:
  - id: UUID
  - group_id: UUID (FK)
  - name: String
  - phone: String (unique per group)
  - role: String (DRIVER, HELPER, MANAGER)
  - created_at: DateTime
```

### Vehicle
```python
Vehicle:
  - id: UUID
  - group_id: UUID (FK)
  - license_plate: String (unique per group)
  - vehicle_type: String (TRUCK, VAN, MOTORCYCLE, CAR)
  - assigned_driver_id: UUID (FK to Driver)
  - created_at: DateTime
```

### Trip
```python
Trip:
  - id: UUID
  - group_id: UUID (FK)
  - vehicle_id: UUID (FK)
  - driver_id: UUID (FK)
  - date: Date
  - trip_number: Integer (auto-increment daily per vehicle)
  - created_at: DateTime
```

### Fuel Record
```python
FuelRecord:
  - id: UUID
  - group_id: UUID (FK)
  - vehicle_id: UUID (FK)
  - date: Date
  - liters: Float
  - cost: Decimal
  - receipt_photo_url: String (optional)
  - created_at: DateTime
```

---

## 2. Bot Commands

### Setup Commands

#### `/register_driver`
**Flow:**
1. Ask: "Enter driver name:"
2. Ask: "Enter phone number:"
3. Ask: "Select role:" → Buttons: [Driver] [Helper] [Manager]
4. Save and confirm

#### `/register_vehicle`
**Flow:**
1. Ask: "Enter license plate (ស្លាកលេខឡាន):"
2. Ask: "Select vehicle type:" → Buttons: [🚚 Truck] [🚐 Van] [🏍️ Motorcycle] [🚗 Car]
3. Ask: "Assign driver:" → Show list of drivers
4. Save and confirm

---

### Daily Operation Commands

#### `/record_trip`
**Flow:**
1. Ask: "Select vehicle:" → Show list of vehicles
2. Auto-record:
   - Current date
   - Auto-increment trip number for today
   - Assigned driver
3. Confirm: "Trip #X recorded for [plate]"

**Example:**
```
✅ Trip #3 recorded for PP-1234
Driver: Sok
Date: 2025-12-03
Time: 14:30

Total trips today: 3
```

#### `/record_fuel`
**Flow:**
1. Ask: "Select vehicle:" → Show list of vehicles
2. Ask: "Enter liters:"
3. Ask: "Enter cost (រៀល):"
4. Ask: "Upload receipt photo (optional):" → Option: [Skip ⏭️]
5. Save and confirm

**Example:**
```
⛽ Fuel recorded for PP-1234
Date: 2025-12-03
Liters: 50L
Cost: 250,000 រៀល
Receipt: ✅ Uploaded
```

#### `/today`
**Quick Daily Overview**

**Flow:**
1. User sends command
2. Bot immediately shows today's summary

**Example:**
```
📊 Today's Summary (2025-12-03)
════════════════════════════

🚚 PP-1234 (Sok)
   Trips: 5
   Fuel: 50L (250,000 រៀល)

🚐 2A-5678 (Dara)
   Trips: 3
   Fuel: 30L (150,000 រៀល)

────────────────────────────
Total Trips: 8
Total Fuel: 80L
Total Cost: 400,000 រៀល
```

---

### Report Commands

#### `/report_daily` or `/report_daily [YYYY-MM-DD]`
**Output:**
```
📊 Daily Report - 2025-12-03
════════════════════════════

🚚 PP-1234 (Driver: Sok)
   Trips: 5
   Fuel: 50L (250,000 រៀល)

🚐 2A-5678 (Driver: Dara)
   Trips: 3
   Fuel: 30L (150,000 រៀល)

────────────────────────────
Total Trips: 8
Total Fuel: 80L
Total Cost: 400,000 រៀល

[Export Excel 📊] [Export PDF 📄]
```

#### `/report_monthly` or `/report_monthly [YYYY-MM]`
**Output:**
```
📊 Monthly Report - December 2025
═════════════════════════════════

🚚 PP-1234 (Driver: Sok)
   Total Trips: 110
   Total Fuel: 980L
   Total Cost: 4,900,000 រៀល
   Avg Trips/Day: 5.0
   Avg Fuel/Trip: 8.9L

🚐 2A-5678 (Driver: Dara)
   Total Trips: 85
   Total Fuel: 650L
   Total Cost: 3,250,000 រៀល
   Avg Trips/Day: 3.9
   Avg Fuel/Trip: 7.6L

─────────────────────────────────
SUMMARY
─────────────────────────────────
Total Vehicles: 2
Total Trips: 195
Total Fuel: 1,630L
Total Cost: 8,150,000 រៀល

[Export Excel 📊] [Export PDF 📄] [View Performance 📈]
```

#### `/report_vehicle [license_plate]`
**Vehicle Performance Analytics**

**Output:**
```
📊 Vehicle Performance - PP-1234
═════════════════════════════════

Vehicle Info:
License: PP-1234
Type: 🚚 Truck
Driver: Sok

─────────────────────────────────
THIS MONTH (December 2025)
─────────────────────────────────
Total Trips: 110
Total Fuel: 980L
Total Cost: 4,900,000 រៀល

Averages:
• Trips per day: 5.0
• Fuel per trip: 8.9L
• Cost per trip: 44,545 រៀល

─────────────────────────────────
LAST 7 DAYS
─────────────────────────────────
Daily breakdown:
Dec 03: 5 trips | 50L | 250,000 រៀល
Dec 02: 6 trips | 55L | 275,000 រៀល
Dec 01: 4 trips | 40L | 200,000 រៀល
Nov 30: 5 trips | 48L | 240,000 រៀល
Nov 29: 7 trips | 62L | 310,000 រៀល
Nov 28: 3 trips | 30L | 150,000 រៀល
Nov 27: 5 trips | 45L | 225,000 រៀល

[Export Excel 📊] [Export PDF 📄]
```

---

## 3. Database Schema

```sql
-- Drivers
CREATE TABLE drivers (
    id UUID PRIMARY KEY,
    group_id UUID NOT NULL REFERENCES groups(id),
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    role VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(group_id, phone)
);

-- Vehicles
CREATE TABLE vehicles (
    id UUID PRIMARY KEY,
    group_id UUID NOT NULL REFERENCES groups(id),
    license_plate VARCHAR(20) NOT NULL,
    vehicle_type VARCHAR(20) NOT NULL,
    assigned_driver_id UUID REFERENCES drivers(id),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(group_id, license_plate)
);

-- Trips
CREATE TABLE trips (
    id UUID PRIMARY KEY,
    group_id UUID NOT NULL REFERENCES groups(id),
    vehicle_id UUID NOT NULL REFERENCES vehicles(id),
    driver_id UUID NOT NULL REFERENCES drivers(id),
    date DATE NOT NULL,
    trip_number INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(vehicle_id, date, trip_number)
);

-- Fuel Records
CREATE TABLE fuel_records (
    id UUID PRIMARY KEY,
    group_id UUID NOT NULL REFERENCES groups(id),
    vehicle_id UUID NOT NULL REFERENCES vehicles(id),
    date DATE NOT NULL,
    liters DECIMAL(10, 2) NOT NULL,
    cost DECIMAL(15, 2) NOT NULL,
    receipt_photo_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_trips_vehicle_date ON trips(vehicle_id, date);
CREATE INDEX idx_fuel_vehicle_date ON fuel_records(vehicle_id, date);
```

---

## 4. Architecture Structure

```
src/
├── domain/
│   ├── entities/
│   │   ├── driver.py
│   │   ├── vehicle.py
│   │   ├── trip.py
│   │   └── fuel_record.py
│   └── repositories/
│       ├── driver_repository.py
│       ├── vehicle_repository.py
│       ├── trip_repository.py
│       └── fuel_record_repository.py
│
├── application/
│   ├── use_cases/
│   │   ├── register_driver.py
│   │   ├── register_vehicle.py
│   │   ├── record_trip.py
│   │   ├── record_fuel.py
│   │   ├── get_daily_report.py
│   │   └── get_monthly_report.py
│   └── dto/
│       └── vehicle_dto.py
│
├── infrastructure/
│   ├── persistence/
│   │   ├── sqlalchemy_driver_repository.py
│   │   ├── sqlalchemy_vehicle_repository.py
│   │   ├── sqlalchemy_trip_repository.py
│   │   └── sqlalchemy_fuel_record_repository.py
│   ├── storage/
│   │   └── photo_storage_service.py (for receipt uploads)
│   └── export/
│       ├── excel_export_service.py
│       └── pdf_export_service.py
│
└── presentation/
    └── handlers/
        ├── vehicle_handler.py (combines all vehicle-related commands)
        └── vehicle_report_handler.py
```

---

## 5. Conversation States

```python
# Driver registration
REGISTER_DRIVER_NAME = 1
REGISTER_DRIVER_PHONE = 2
REGISTER_DRIVER_ROLE = 3

# Vehicle registration
REGISTER_VEHICLE_PLATE = 10
REGISTER_VEHICLE_TYPE = 11
REGISTER_VEHICLE_DRIVER = 12

# Trip recording
RECORD_TRIP_SELECT_VEHICLE = 20

# Fuel recording
RECORD_FUEL_SELECT_VEHICLE = 30
RECORD_FUEL_LITERS = 31
RECORD_FUEL_COST = 32
RECORD_FUEL_PHOTO = 33
```

---

## 6. Implementation Steps

### Step 1: Database Setup
- [ ] Create migration files for 4 tables
- [ ] Run migrations

### Step 2: Domain Layer
- [ ] Create entities (Driver, Vehicle, Trip, FuelRecord)
- [ ] Create repository interfaces

### Step 3: Infrastructure Layer
- [ ] Implement SQLAlchemy repositories
- [ ] Add database models

### Step 4: Application Layer
- [ ] Implement use cases (8 total: register_driver, register_vehicle, record_trip, record_fuel, get_daily_report, get_monthly_report, get_vehicle_performance, export_report)
- [ ] Create DTOs
- [ ] Implement photo storage service (S3 or similar)

### Step 5: Presentation Layer
- [ ] Create vehicle_handler.py with conversation flows
- [ ] Create vehicle_report_handler.py for reports
- [ ] Register handlers in main.py

### Step 6: Testing
- [ ] Test driver registration
- [ ] Test vehicle registration
- [ ] Test trip recording (verify auto-increment)
- [ ] Test fuel recording
- [ ] Test daily report
- [ ] Test monthly report

---

## 7. Validation Rules

**Driver:**
- Name: Required, max 100 chars
- Phone: Required, unique per group
- Role: Must be DRIVER, HELPER, or MANAGER

**Vehicle:**
- License plate: Required, unique per group, max 20 chars
- Vehicle type: Required, must be TRUCK, VAN, MOTORCYCLE, or CAR
- Driver: Must exist

**Trip:**
- Vehicle: Must exist
- Trip number: Auto-generated (max for date + 1)

**Fuel:**
- Liters: Required, positive number
- Cost: Required, positive number
- Receipt photo: Optional, image file types (JPG, PNG)

---

## 8. Business Logic

### Auto-increment Trip Numbers
```python
# When recording a trip:
# 1. Get max trip_number for vehicle on date
# 2. New trip_number = max + 1 (or 1 if no trips today)
# 3. Resets to 1 every day per vehicle
```

### Report Calculations
```python
# Daily Report:
# - Count trips per vehicle for date
# - Sum fuel liters and cost per vehicle for date
# - Grand totals

# Monthly Report:
# - Count trips per vehicle for month
# - Sum fuel per vehicle for month
# - Calculate averages:
#   - Avg trips/day = total trips / days in month
#   - Avg fuel/trip = total fuel / total trips
```

---

## Future Enhancements (Phase 2+)

These features are NOT in Phase 1 but can be added later:
- Trip details (destination, distance, load description)
- GPS tracking and route mapping
- Maintenance tracking and service reminders
- Automated daily/weekly/monthly notifications
- Multi-month trend comparisons
- Driver performance scoring
- Cost optimization suggestions

---

## Summary

**Phase 1 Scope:**
- Driver registration (Name, Phone, Role)
- Vehicle registration (License plate, Type, Driver assignment)
- Trip recording (auto-increment counter per vehicle per day)
- Fuel tracking (liters, cost, receipt photo upload)
- Quick daily overview (/today command)
- Daily and monthly reports
- Vehicle performance analytics
- Excel and PDF export functionality
- All operations via Telegram bot commands

**Out of Scope for Phase 1:**
- Complex trip details (destination, distance, load) - Phase 2
- GPS/location tracking - Phase 2
- Maintenance tracking - Phase 2
- Automated notifications - Phase 2
- Multi-month comparisons - Phase 2
