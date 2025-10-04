# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2025-10-04

### Added
- **Group Management System**
  - Added `groups` table to store Telegram group information
  - Added `employee_groups` junction table for many-to-many relationship between employees and groups
  - Groups are automatically created when employees check in
  - Employees are automatically added to groups on first check-in

- **Group-Based Check-Ins**
  - Check-ins now reference a specific group
  - Check-ins must be performed in group chats (not private chats)
  - Added `group_id` foreign key to `check_ins` table
  - Bot automatically registers groups and associates employees

- **Domain Entities**
  - `Group` entity for managing organization groups
  - `EmployeeGroup` entity for employee-group associations

- **Repositories**
  - `IGroupRepository` and `GroupRepository` implementation
  - `IEmployeeGroupRepository` and `EmployeeGroupRepository` implementation

- **Use Cases**
  - `RegisterGroupUseCase` - Register or retrieve groups
  - `AddEmployeeToGroupUseCase` - Add employees to groups

### Changed
- **CheckIn Entity**
  - Now requires `group_id` parameter
  - Updated factory method to include group reference

- **RecordCheckInUseCase**
  - Now requires `IGroupRepository` dependency
  - Validates group existence before recording check-in

- **CheckInHandler**
  - Enforces group chat requirement for check-ins
  - Automatically handles group registration
  - Automatically handles employee-group association

### Database Migration
- Migration `002_add_groups_and_employee_groups.py`
  - Creates `groups` table
  - Creates `employee_groups` table
  - Adds `group_id` column to `check_ins` table with foreign key constraint

## [1.0.0] - 2025-10-03

### Added
- Initial release with basic features
- Employee registration
- Check-in with location sharing
- Salary advance recording (admin only)
- DDD architecture implementation
- MySQL database support
- Alembic migrations
