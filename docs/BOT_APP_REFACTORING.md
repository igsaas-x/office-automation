# Bot Application Refactoring

## Overview

The `bot_app.py` file was refactored from **1016 lines** to **444 lines** to comply with the 800-line file size limit rule.

## Architecture

All handler wrapper functions have been extracted into separate modules organized by functionality under `src/infrastructure/telegram/wrappers/`.

## Module Structure

### 1. `employee_wrappers.py` (92 lines)
Handles employee registration and management:
- `start_wrapper` - Start conversation with employee
- `register_wrapper` - Register employee
- `register_command_wrapper` - Handle /register command
- `request_advance_placeholder` - Placeholder for advance requests

### 2. `salary_wrappers.py` (68 lines)
Handles salary advance recording:
- `salary_advance_start_wrapper` - Start salary advance flow
- `salary_advance_amount_wrapper` - Get advance amount
- `salary_advance_note_wrapper` - Get advance note
- `salary_advance_save_wrapper` - Save salary advance

### 3. `registration_wrappers.py` (65 lines)
Handles group registration for businesses:
- `register_group_start_wrapper` - Start group registration
- `register_group_receive_name_wrapper` - Receive business name

### 4. `menu_wrappers.py` (246 lines)
Handles menu navigation and check-in reports:
- `menu_wrapper` - Show main menu
- `report_command_wrapper` - Handle /report command
- `menu_reports_callback_wrapper` - Show report selection
- `report_daily_callback_wrapper` - Show daily report
- `report_monthly_callback_wrapper` - Show monthly report
- `back_to_main_menu_wrapper` - Navigate back to main menu
- `back_to_menu_wrapper` - Navigate back to vehicle menu
- `show_daily_operation_menu_wrapper` - Show daily operations
- `show_report_menu_wrapper` - Show report menu
- `cancel_menu_wrapper` - Cancel menu

### 5. `setup_wrappers.py` (146 lines)
Handles vehicle and driver setup:
- `setup_menu_wrapper` - Show setup menu
- `setup_vehicle_start_wrapper` - Start vehicle setup
- `setup_vehicle_plate_wrapper` - Receive vehicle plate
- `setup_vehicle_driver_wrapper` - Receive vehicle driver
- `setup_driver_*_wrapper` - Driver setup handlers
- `setup_list_vehicles_wrapper` - List all vehicles
- `setup_delete_vehicle_wrapper` - Delete vehicle
- `cancel_setup_wrapper` - Cancel setup

### 6. `vehicle_operations_wrappers.py` (134 lines)
Handles trip and fuel recording:
- Trip recording handlers:
  - `start_trip_recording_wrapper`
  - `select_trip_vehicle_wrapper`
  - `receive_trip_count_wrapper`
  - `receive_total_loading_size_wrapper`
- Fuel recording handlers:
  - `start_fuel_recording_wrapper`
  - `select_fuel_vehicle_wrapper`
  - `receive_fuel_liters_wrapper`
  - `receive_fuel_cost_wrapper`
  - `complete_fuel_record_wrapper`

### 7. `report_wrappers.py` (87 lines)
Handles vehicle logistics reports:
- `show_daily_report_wrapper` - Daily logistics report
- `show_monthly_report_wrapper` - Monthly logistics report
- `start_vehicle_performance_wrapper` - Start performance report
- `show_vehicle_performance_wrapper` - Show performance report
- `export_placeholder_wrapper` - Export placeholder

## Design Pattern

Each wrapper module uses a **factory function pattern**:

```python
def create_*_wrappers(get_repositories_func, [additional_params]):
    """
    Create handler wrappers

    Args:
        get_repositories_func: Function that returns repository instances
        [additional_params]: Optional additional dependencies

    Returns:
        Dict of wrapper functions
    """

    async def some_wrapper(update, context):
        # Handler logic
        pass

    return {
        'some_wrapper': some_wrapper,
        # ...
    }
```

## Benefits

1. **Maintainability**: Each module focuses on a specific domain (employees, reports, etc.)
2. **Testability**: Individual wrapper modules can be tested independently
3. **Readability**: Smaller files are easier to understand and navigate
4. **Compliance**: All files are under 800 lines as required
5. **Separation of Concerns**: Clear boundaries between different bot functionalities

## File Size Compliance

All files now comply with the 800-line limit:

| File | Lines |
|------|-------|
| `bot_app.py` | 444 |
| `employee_wrappers.py` | 92 |
| `salary_wrappers.py` | 68 |
| `registration_wrappers.py` | 65 |
| `menu_wrappers.py` | 246 |
| `setup_wrappers.py` | 146 |
| `vehicle_operations_wrappers.py` | 134 |
| `report_wrappers.py` | 87 |

## Migration Notes

- All wrapper functions maintain the same signatures and behavior
- No changes to bot functionality or user experience
- Repository injection pattern preserved
- Session management handled consistently across all wrappers
