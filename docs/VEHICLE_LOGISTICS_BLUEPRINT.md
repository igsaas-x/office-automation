# Vehicle Logistics Tracking - Blueprint (Phase 1)

## Overview

Simple vehicle trip and fuel tracking system for logistics operations via Telegram bot.

---

## Core Requirements - Phase 1

### Setup
1. Register vehicles (License plate/ស្លាកលេខឡាន, Type)
2. Register drivers (Name, Phone, assign to Vehicle) - Role defaults to DRIVER

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

### Vehicle
```python
Vehicle:
  - id: UUID
  - group_id: UUID (FK)
  - license_plate: String (unique per group)
  - vehicle_type: String (TRUCK, VAN, MOTORCYCLE, CAR)
  - created_at: DateTime
```

### Driver
```python
Driver:
  - id: UUID
  - group_id: UUID (FK)
  - name: String
  - phone: String (unique per group)
  - role: String (defaults to DRIVER in Phase 1)
  - assigned_vehicle_id: UUID (FK to Vehicle, optional)
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

## 2. Bot Menu Structure

### Command Hierarchy

```
Level 1 (Commands):
├── /register (existing - employee registration)
├── /setup
└── /menu

Level 2+ (Buttons):
/setup
├── [Setup Vehicle 🚗]
└── [Setup Driver 👤]

/menu
├── [📍 Check In] (existing feature - with feature flag)
├── [📋 Daily Operation]
│   ├── [⛽ Add Fuel Record]
│   └── [🚚 Add Trip Record]
└── [📊 Report]
    ├── [📅 Daily Report]
    └── [📆 Monthly Report]
```

---

### `/register` (Existing)
Employee registration - keep as is.

---

### `/setup`
**Setup Menu**

**Flow:**
1. User sends `/setup`
2. Bot shows setup options:

```
⚙️ Setup Menu

Choose what to setup:

[Setup Vehicle 🚗] [Setup Driver 👤]

Note: Set up vehicles first, then drivers
```

#### Setup Driver Flow (Button: "Setup Driver 👤")
**Flow:**
1. User clicks "Setup Driver 👤"
2. Ask: "Enter driver name:"
3. Ask: "Enter phone number:"
4. Ask: "Assign to vehicle:" → Show list of vehicles
5. Save and confirm (role defaults to DRIVER)

**Note:** Vehicles should be set up first before adding drivers.

#### Setup Vehicle Flow (Button: "Setup Vehicle 🚗")
**Flow:**
1. User clicks "Setup Vehicle 🚗"
2. Ask: "Enter license plate (ស្លាកលេខឡាន):"
3. Save and confirm

**Note:** Driver will be assigned when creating the driver.

---

### `/menu`
**Main Menu**

**Flow:**
1. User sends `/menu`
2. Bot shows main menu:

```
🏠 Main Menu

[📍 Check In]

📋 Daily Operation
[⛽ Add Fuel Record] [🚚 Add Trip Record]

📊 Report
[📅 Daily Report] [📆 Monthly Report]
```

**Note:** The "📍 Check In" button has a feature flag to enable/disable per group.

---

#### Add Fuel Record (Button: "⛽ Add Fuel Record")
**Flow:**
1. User clicks "⛽ Add Fuel Record"
2. Ask: "Select vehicle:" → Show list of vehicles
3. Ask: "Enter liters:"
4. Ask: "Enter cost (រៀល)/(Dollar):"
5. Ask: "Upload receipt photo (optional):" → Option: [Skip ⏭️]
6. Save and confirm

**Example:**
```
⛽ Fuel recorded for PP-1234
Date: 2025-12-03
Liters: 50L
Cost: 250,000 រៀល
Receipt: ✅ Uploaded

[Back to Menu 🏠]
```

---

#### Add Trip Record (Button: "🚚 Add Trip Record")
**Flow:**
1. User clicks "🚚 Add Trip Record"
2. Ask: "Select vehicle:" → Show list of vehicles
3. Auto-record:
   - Current date
   - Auto-increment trip number for today
   - Assigned driver
4. Confirm with back button

**Example:**
```
✅ Trip #3 recorded for PP-1234
Driver: Sok
Date: 2025-12-03
Time: 14:30

Total trips today: 3

[Back to Menu 🏠]
```

---

#### Daily Report (Button: "📅 Daily Report")
**Flow:**
1. User clicks "📅 Daily Report"
2. Bot shows today's report:

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
[📆 View Other Date] [Back to Menu 🏠]
```

---

#### Monthly Report (Button: "📆 Monthly Report")
**Flow:**
1. User clicks "📆 Monthly Report"
2. Bot shows current month report:

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

[Export Excel 📊] [Export PDF 📄]
[📈 Vehicle Performance] [Back to Menu 🏠]
```

---

#### Vehicle Performance (Button: "📈 Vehicle Performance")
**Flow:**
1. User clicks "📈 Vehicle Performance"
2. Bot shows vehicle selection:
   ```
   Select vehicle to view performance:

   [🚚 PP-1234 (Sok)]
   [🚐 2A-5678 (Dara)]

   [Back to Menu 🏠]
   ```
3. User selects vehicle
4. Bot shows performance report:

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
[Back to Menu 🏠]
```

---

## 3. Database Schema

```sql
-- Vehicles (created first)
CREATE TABLE vehicles (
    id UUID PRIMARY KEY,
    group_id UUID NOT NULL REFERENCES groups(id),
    license_plate VARCHAR(20) NOT NULL,
    vehicle_type VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(group_id, license_plate)
);

-- Drivers (created after vehicles, assigned to vehicle)
CREATE TABLE drivers (
    id UUID PRIMARY KEY,
    group_id UUID NOT NULL REFERENCES groups(id),
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'DRIVER',
    assigned_vehicle_id UUID REFERENCES vehicles(id),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(group_id, phone)
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
        ├── menu_handler.py (handles /menu command and navigation)
        ├── setup_handler.py (handles /setup command and submenus)
        ├── vehicle_handler.py (trip and fuel recording logic)
        └── report_handler.py (all report generation)
```

---

## 5. Conversation States

```python
# Menu states
MAIN_MENU = 0
SETUP_MENU = 1
DAILY_OPERATION_MENU = 2
REPORT_MENU = 3

# Setup - Vehicle registration (comes first)
SETUP_VEHICLE_PLATE = 10
SETUP_VEHICLE_TYPE = 11

# Setup - Driver registration (comes after vehicles)
SETUP_DRIVER_NAME = 20
SETUP_DRIVER_PHONE = 21
SETUP_DRIVER_VEHICLE = 22  # Select vehicle to assign

# Daily Operation - Trip recording
RECORD_TRIP_SELECT_VEHICLE = 30

# Daily Operation - Fuel recording
RECORD_FUEL_SELECT_VEHICLE = 40
RECORD_FUEL_LITERS = 41
RECORD_FUEL_COST = 42
RECORD_FUEL_PHOTO = 43

# Reports
REPORT_DAILY_SELECT_DATE = 50
REPORT_MONTHLY_SELECT_MONTH = 51
REPORT_VEHICLE_SELECT = 52
```

---

## 6. Feature Flags

### Check-In Feature Toggle

The "📍 Check In" button in the `/menu` command should have a feature flag to enable/disable it per group.

**Implementation:**
```python
# In Group entity or settings table
Group:
  - checkin_enabled: Boolean (default: True)

# Or in a separate feature_flags table
FeatureFlags:
  - group_id: UUID
  - feature_name: String
  - enabled: Boolean
```

**Usage:**
```python
# When showing /menu
def show_menu(group_id):
    buttons = []

    # Check if check-in is enabled for this group
    if is_feature_enabled(group_id, 'checkin'):
        buttons.append([InlineKeyboardButton("📍 Check In", callback_data="checkin")])

    # Always show other features
    buttons.append([
        InlineKeyboardButton("⛽ Add Fuel Record", callback_data="add_fuel"),
        InlineKeyboardButton("🚚 Add Trip Record", callback_data="add_trip")
    ])
    ...
```

**Admin Command (Optional):**
```
/admin_toggle_feature checkin
→ Toggle check-in feature on/off for current group
```

---

## 7. Implementation Steps

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
- [ ] Create menu_handler.py (/menu command with navigation)
- [ ] Create setup_handler.py (/setup command with submenus)
- [ ] Create vehicle_handler.py (trip and fuel recording)
- [ ] Create report_handler.py (all reports)
- [ ] Implement feature flag for check-in button
- [ ] Register all handlers in main.py

### Step 6: Testing
- [ ] Test /setup command navigation
- [ ] Test driver registration via Setup menu
- [ ] Test vehicle registration via Setup menu
- [ ] Test /menu command navigation
- [ ] Test trip recording via Daily Operation menu (verify auto-increment)
- [ ] Test fuel recording via Daily Operation menu (with photo upload)
- [ ] Test daily report via Report menu
- [ ] Test monthly report via Report menu
- [ ] Test vehicle performance report
- [ ] Test feature flag (check-in button toggle)
- [ ] Test Excel and PDF export

---

## 8. Validation Rules

**Driver:**
- Name: Required, max 100 chars
- Phone: Required, unique per group
- Role: Auto-set to DRIVER (Phase 1)
- Vehicle: Optional (can assign later)

**Vehicle:**
- License plate: Required, unique per group, max 20 chars
- Vehicle type: Required, must be TRUCK, VAN, MOTORCYCLE, or CAR

**Trip:**
- Vehicle: Must exist
- Trip number: Auto-generated (max for date + 1)

**Fuel:**
- Liters: Required, positive number
- Cost: Required, positive number
- Receipt photo: Optional, image file types (JPG, PNG)

---

## 9. Business Logic

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
- Vehicle registration first (License plate, Type)
- Driver registration (Name, Phone, assign to Vehicle) - Role defaults to DRIVER
- Trip recording (auto-increment counter per vehicle per day)
- Fuel tracking (liters, cost, receipt photo upload)
- Daily and monthly reports via /menu
- Vehicle performance analytics
- Excel and PDF export functionality
- Menu-driven navigation (/setup, /menu)
- Feature flag for check-in button

**Out of Scope for Phase 1:**
- Multiple driver roles (HELPER, MANAGER) - Phase 2
- Complex trip details (destination, distance, load) - Phase 2
- GPS/location tracking - Phase 2
- Maintenance tracking - Phase 2
- Automated notifications - Phase 2
- Multi-month comparisons - Phase 2
