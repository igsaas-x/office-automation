# Employee Management System - Blueprint

## System Overview

This document outlines the complete flow for the Office Automation (OA) Employee Management System, covering business admin operations, Autosum admin operations, and technical implementation details.

---

## Quick Start Summary

### Visual Flow

```
BUSINESS ADMIN JOURNEY
═══════════════════════════════════════════════════════════════

PHASE A: SETUP (One-time, 5 minutes)
┌─────────────────────────────────────────────────────────────┐
│  In Telegram App                                            │
│  ─────────────────────────────────────────────────────────  │
│  1. Create Telegram group                                   │
│  2. Add @OALocal_bot to group                               │
│  3. Run command: /register                                  │
│  4. Enter business/branch name                              │
│  5. Receive unique mini app link                            │
│  6. Pin the link message                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Setup Complete
                              ↓
PHASE B: DAILY USAGE (Ongoing)
┌─────────────────────────────────────────────────────────────┐
│  In Mini App (Web Interface)                                │
│  ─────────────────────────────────────────────────────────  │
│  • Open from pinned link (group auto-selected)              │
│  • Register employees (with name, phone, role, salary)      │
│  • Review employee check-ins                                │
│  • Approve/reject salary advances                           │
│  • Record allowances (transport, meal, overtime)            │
│  • Generate reports and export data                         │
└─────────────────────────────────────────────────────────────┘

IMPORTANT NOTES:
─────────────────
✓ Employees do NOT need to be in the Telegram group
✓ Employees do NOT need a Telegram account (optional)
✓ Each group gets its own unique mini app link
✓ Opening from link = automatic group selection (no manual picking)
```

### For Business Admins

**Phase A: One-Time Setup (5 minutes, via Telegram Bot)**
1. Create a Telegram group for your business/branch
2. Add @OALocal_bot to the group
3. Run `/register` command
4. Enter your business/branch name
5. Receive and pin your unique mini app link

**Phase B: Daily Operations (via Mini App)**
- Open mini app from pinned link (auto-selects your group)
- Register employees (no need to add them to Telegram group)
- Review check-ins, approve advances, manage allowances
- Generate reports and export data

### For Autosum Admins

**Manage System via Bot Commands:**
- Update customer packages: `/admin_update_package`
- Configure positions/roles: `/admin_add_position`
- Enable/disable features: `/admin_enable_feature`
- View system stats: `/admin_stats`

---

## 1. Business Admin Flow

The business admin workflow is divided into two distinct phases:
- **Phase A: Setup (via Bot)** - One-time configuration in Telegram group
- **Phase B: Daily Usage (via Mini App)** - All employee management operations

**Key Principle:**
- Telegram group = Management hub for admins (bot commands)
- Mini App = All employee operations (register, check-in, advances, reports)
- Employees do NOT need to be in the Telegram group

---

## Phase A: Setup (Bot Commands in Telegram Group)

This is a one-time setup process done entirely through the Telegram bot in the group chat.

### Step 1: Create Telegram Group

**Objective:** Set up a Telegram group as the management hub for the business/branch.

**Actions:**
1. Business admin creates a new Telegram group
2. Names the group appropriately (e.g., "ABC Company - Main Branch", "XYZ Corp - Phnom Penh")
3. Adds other managers/admins to the group (optional)

**Important Notes:**
- **Employees do NOT need to be added to this Telegram group**
- This group is for business admins to manage the system
- Employee registration will happen later in the mini app

**Technical Notes:**
- Group identified by unique `chat_id` in the system
- Stored in `groups` table

---

### Step 2: Add OA Bot to Group

**Objective:** Add the OA bot to enable the system in this group.

**Actions:**
1. Business admin adds @OALocal_bot to the group
2. Bot automatically receives necessary permissions

**Bot Response:**
```
👋 Hello! I'm the OA Bot.

To register this group as a business, please run:
/register
```

**Technical Notes:**
- Bot receives group `chat_id` upon joining
- Bot starts listening for the `/register` command

---

### Step 3: Register Group with `/register` Command

**Objective:** Register the group as a business/branch and receive the mini app link.

**Actions:**
1. Admin runs `/register` command in the group
2. Bot prompts for business/branch name
3. Admin provides the name
4. Bot confirms registration and provides the group-specific mini app link

**Example Interaction:**
```
Admin: /register

Bot: 📝 Please enter your business or branch name:

Admin: ABC Company - Main Branch

Bot: ✅ Registration successful!

Business Name: ABC Company - Main Branch
Group ID: -1001234567890
Package: Free (contact @AutosumSupport to upgrade)

🔗 Your Mini App Link (pin this message):
https://t.me/OALocal_bot/app?startapp=group_1001234567890

[Button: Open Mini App]

All employee management operations should be done through this mini app.
📌 Tip: Pin this message for easy access!
```

**Data Stored:**
- `groups` table: `chat_id`, `name`, `business_name`, `created_at`
- Default `package_level`: 'free'

**Technical Implementation:**
```python
# File: src/presentation/handlers/registration_handler.py

async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /register command in group"""
    chat = update.effective_chat

    # Only works in group chats
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text(
            "⛔ This command only works in group chats."
        )
        return

    # Check if already registered
    existing = group_repository.get_by_chat_id(chat.id)
    if existing:
        await update.message.reply_text(
            f"✅ This group is already registered as:\n"
            f"**{existing.business_name}**\n\n"
            f"Mini App: https://t.me/{context.bot.username}/app?startapp=group_{abs(chat.id)}"
        )
        return

    # Prompt for business name
    await update.message.reply_text(
        "📝 Please enter your business or branch name:"
    )

    # Set conversation state (use ConversationHandler)
    return WAITING_FOR_BUSINESS_NAME

async def receive_business_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and save business name"""
    business_name = update.message.text.strip()
    chat = update.effective_chat

    # Save to database
    group = group_repository.create_group(
        chat_id=chat.id,
        name=chat.title,
        business_name=business_name,
        package_level='free'
    )

    # Generate mini app deep link
    deep_link = f"https://t.me/{context.bot.username}/app?startapp=group_{abs(chat.id)}"

    # Send confirmation with mini app link
    keyboard = [[InlineKeyboardButton("🚀 Open Mini App", url=deep_link)]]

    await update.message.reply_text(
        f"✅ Registration successful!\n\n"
        f"**Business Name:** {business_name}\n"
        f"**Group ID:** {chat.id}\n"
        f"**Package:** Free (contact @AutosumSupport to upgrade)\n\n"
        f"🔗 **Your Mini App Link:**\n{deep_link}\n\n"
        f"All employee management operations should be done through this mini app.\n"
        f"📌 **Tip:** Pin this message for easy access!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

    return ConversationHandler.END
```

---

### Step 4: Pin the Mini App Link

**Objective:** Make the mini app easily accessible to all group admins.

**Actions:**
1. Admin pins the bot's message containing the mini app link
2. All group members can now access the mini app with one tap

**Result:**
- Group setup is complete
- Admins can now proceed to Phase B (daily usage via mini app)

---

### Step 5: Upgrade Package (Optional)

**Objective:** Unlock additional features by upgrading to a paid package.

**Actions:**
1. Business admin contacts Autosum team (@AutosumSupport or support contact)
2. Discusses needs and selects appropriate package:
   - **Free:** Basic check-in, employee registry (max 10 employees)
   - **Basic ($X/month):** Up to 50 employees, salary advances, allowances, leave management
   - **Premium ($X/month):** Unlimited employees, Google Sheets integration, advanced analytics, custom reports
3. Autosum admin updates package (see Section 2.1)

**Payment Methods:**
- Bank transfer
- Mobile payment (Wing, ABA Pay)
- Future: In-app payment integration

**Technical Notes:**
- Package level determines feature access
- Autosum admin updates via admin bot commands

---

## Phase B: Daily Usage (Mini App)

All employee management and daily operations are performed through the mini app, not in the Telegram group.

### Access Mini App

**Methods:**
1. **From Pinned Message:** Tap the "Open Mini App" button in the pinned message
2. **Direct Link:** Use the group-specific link: `https://t.me/OALocal_bot/app?startapp=group_<chat_id>`
3. **Bot Menu:** Message the bot `/start` → Click "Open Mini App" (will need to select group)

**Auto Group Selection:**
- When opening from the group-specific link, the mini app automatically selects that group
- No manual group selection needed

---

### 1. Register Employees

**Objective:** Add employees to the system for tracking and management.

**Steps:**
1. Open mini app from the group's pinned link
2. Navigate to "Employee Management" → "Add Employee"
3. For each employee, enter:
   - Full name
   - Phone number
   - Telegram username (optional, for auto-detection)
   - Role/Position (select from dropdown)
   - Date started work
   - Probation period (months)
   - Base salary
   - Bonus amount (optional)
4. Click "Save Employee"

**Data Stored:**
- `employees` table: All employee details
- `employee_groups` table: Links employee to this group (M2M relationship)

**Important Notes:**
- Employees do **NOT** need to be in the Telegram group
- Employees do **NOT** need a Telegram account (though it's recommended for check-ins)
- Employees can be registered manually by admin with just name and phone

**Technical Implementation:**
- API endpoint: `POST /api/employees`
- Authentication: Telegram Web App signature verification
- Validation: Phone number format, salary > 0, etc.

**Example API Request:**
```json
POST /api/employees
{
  "group_chat_id": "-1001234567890",
  "name": "John Doe",
  "phone": "+85512345678",
  "telegram_username": "johndoe",
  "role": "Driver",
  "date_start_work": "2025-01-15",
  "probation_months": 3,
  "base_salary": 500.00,
  "bonus": 50.00
}
```

---

### 2. Manage Employees

**Objective:** View, edit, and manage employee records.

**Available Operations:**

#### A. View Employee Directory
- See all employees registered in this group
- Filter by role, status, probation status
- Search by name or phone
- View employee details (salary, start date, etc.)

#### B. Edit Employee Details
- Update any employee information
- Change role/position
- Adjust salary and bonus
- Extend probation period

#### C. Deactivate/Reactivate Employees
- Mark employee as inactive (e.g., resigned, terminated)
- Reactivate employee if needed
- Inactive employees hidden from daily operations but preserved in history

#### D. View Employee Statistics
- Total employees
- Active vs. inactive
- By role breakdown
- On probation count

---

### 3. Check-In Management

**Objective:** Monitor and review employee attendance through location-based check-ins.

**Available Operations:**

#### A. View Daily Check-Ins
- See all check-ins for today across all employees
- Filter by date range
- Sort by time, employee name, or location

#### B. Review Check-In Details
- View check-in photo
- See GPS coordinates on map
- Check timestamp
- Verify employee identity

#### C. Employee Check-In Process
When employees check in (via their own Telegram mini app access):
1. Employee opens mini app
2. Taps "Check In" button
3. App requests camera and location permissions
4. Employee takes a selfie photo
5. App captures GPS coordinates
6. Submit check-in

**Data Captured:**
- Employee ID
- Group/business ID
- GPS coordinates (latitude, longitude)
- Photo
- Timestamp
- Stored in `check_ins` table

#### D. Export Check-In Reports
- Export to CSV
- Export to PDF
- Export to Google Sheets (Premium feature)
- Date range selection
- Filter by employee or role

**Technical Implementation:**
- API endpoint: `POST /api/checkin`
- Max file upload: 16MB (for photos)
- Image optimization: Pillow library
- Google Sheets integration: `gspread` library

---

### 4. Salary Advance Management

**Objective:** Process and track employee salary advance requests.

**Available Operations:**

#### A. View Advance Requests
- See all pending requests
- View approved/rejected history
- Filter by employee, date, status

#### B. Approve/Reject Requests
- Review request details (amount, reason)
- Set approval notes
- Track who approved/rejected
- Send notification to employee

#### C. Set Approval Limits (Premium)
- Define max advance amount per role
- Set monthly advance limits
- Auto-approve within limits
- Require manual approval for over-limit requests

#### D. Track Advances Per Employee
- View total advances given
- See outstanding balance
- Calculate deductions for next payroll
- View repayment history

**Data Stored:**
- `salary_advances` table
- Fields: `employee_id`, `amount`, `note`, `created_by`, `timestamp`, `status`, `approved_by`

**Technical Implementation:**
- API endpoint: `POST /api/salary-advances`
- API endpoint: `PUT /api/salary-advances/{id}/approve`
- API endpoint: `PUT /api/salary-advances/{id}/reject`

---

### 5. Allowances Management

**Objective:** Record and track various employee allowances.

**Allowance Types:**
- Transport allowance
- Meal allowance
- Overtime pay
- Performance bonus
- Holiday bonus
- Other allowances

**Available Operations:**

#### A. Record Allowances
- Select employee
- Choose allowance type
- Enter amount
- Add notes/description
- Submit record

#### B. View Allowance History
- See all allowances by employee
- Filter by type and date range
- View monthly summaries
- Calculate totals

#### C. Bulk Allowance Entry (Premium)
- Add same allowance to multiple employees
- Import from CSV
- Monthly recurring allowances

**Data Stored:**
- `allowances` table
- Fields: `employee_id`, `amount`, `allowance_type`, `note`, `created_by`, `timestamp`

**Technical Implementation:**
- API endpoint: `POST /api/allowances`
- API endpoint: `GET /api/allowances?employee_id={id}&type={type}`

---

### 6. Reports & Analytics

**Objective:** Generate insights and export data for business analysis.

**Available Reports:**

#### A. Attendance Report
- Daily/weekly/monthly attendance
- Check-in success rate
- Late check-ins
- Missing check-ins

#### B. Salary Summary Report
- Base salary totals
- Advances given
- Allowances breakdown
- Net payable amount

#### C. Employee Performance Metrics (Premium)
- Attendance rate by employee
- Punctuality score
- Advances vs. salary ratio
- Custom metrics

#### D. Export Options
- CSV export (all packages)
- PDF export (Basic and above)
- Google Sheets sync (Premium)
- Email reports (Premium)

**Technical Implementation:**
- Google Sheets integration: `gspread` library
- PDF generation: ReportLab or similar
- Export API: `GET /api/reports/{type}?format={csv|pdf|json}`

---

### 7. Multi-Group Management

**For Users Managing Multiple Groups:**

If a user has access to multiple groups/businesses, they can:

1. **Use Group-Specific Links** - Each group has its own unique mini app link (from the `/register` step in Phase A)
2. **Pin Links in Each Group** - Each Telegram group has the link pinned for easy access
3. **Automatic Group Selection** - Opening the mini app from a group-specific link automatically selects that group
4. **Manual Selection** - Users can also switch between groups within the mini app

**How It Works:**
- See **Phase A: Setup → Step 3** for how group-specific links are generated
- Each link contains a `startapp` parameter with the group ID
- The mini app JavaScript parses this parameter and pre-selects the group
- Users never need to manually select a group when opening from the pinned link

**Example:**
- ABC Company link: `https://t.me/OALocal_bot/app?startapp=group_1001234567890`
- XYZ Corp link: `https://t.me/OALocal_bot/app?startapp=group_1009876543210`

Both links go to the same mini app, but automatically select the correct business context.

---

## 2. Autosum Admin Flow

### 2.1 Update Package for Customer

**Objective:** Upgrade or downgrade business packages based on customer requests.

**Current Process:**
1. Receive package update request from business admin
2. Manually update database (direct SQL or admin panel)

**Proposed Bot Command:**
```
/admin_update_package
Group: [Select from dropdown or enter chat_id]
New Package: [Free / Basic / Premium]
Reason: [Enter reason]
```

**Implementation Needed:**

Add admin command handler:
```python
# File: src/presentation/handlers/admin_handler.py

async def update_package_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Check if user is admin
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("⛔ You are not authorized to use this command.")
        return

    # Show group selection keyboard
    groups = group_repository.get_all_groups()
    keyboard = [[InlineKeyboardButton(g.name, callback_data=f"pkg_{g.chat_id}")] for g in groups]
    await update.message.reply_text(
        "Select a group to update package:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Callback handler
async def package_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.data.replace("pkg_", "")

    # Show package options
    keyboard = [
        [InlineKeyboardButton("Free", callback_data=f"set_free_{chat_id}")],
        [InlineKeyboardButton("Basic", callback_data=f"set_basic_{chat_id}")],
        [InlineKeyboardButton("Premium", callback_data=f"set_premium_{chat_id}")]
    ]
    await query.edit_message_text(
        f"Select package for group {chat_id}:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Update database
async def set_package_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.split("_")
    package = data[1]  # free, basic, premium
    chat_id = data[2]

    # Update in database
    group_repository.update_package(chat_id, package)

    await query.edit_message_text(f"✅ Package updated to {package.upper()} for group {chat_id}")
```

**Database Changes Needed:**
```sql
ALTER TABLE groups ADD COLUMN package_level VARCHAR(20) DEFAULT 'free';
ALTER TABLE groups ADD COLUMN package_updated_at TIMESTAMP NULL;
ALTER TABLE groups ADD COLUMN package_updated_by BIGINT NULL;
```

**Feature Access Control:**

Implement package-based feature gating:
```python
# File: src/application/use_cases/check_package_access.py

class CheckPackageAccessUseCase:
    FEATURE_REQUIREMENTS = {
        'check_in': 'free',
        'salary_advance': 'basic',
        'allowances': 'basic',
        'google_sheets_export': 'premium',
        'advanced_reports': 'premium',
        'custom_fields': 'premium'
    }

    PACKAGE_HIERARCHY = {
        'free': 1,
        'basic': 2,
        'premium': 3
    }

    def can_access_feature(self, group_package: str, feature: str) -> bool:
        required_package = self.FEATURE_REQUIREMENTS.get(feature, 'free')
        return self.PACKAGE_HIERARCHY[group_package] >= self.PACKAGE_HIERARCHY[required_package]
```

---

### 2.2 Update Position Configuration

**Objective:** Manage available roles/positions that businesses can assign to employees.

**Current State:**
- Roles are stored as free-text in `employees.role` field
- No validation or standardization

**Proposed Implementation:**

#### A. Create Positions Table

```sql
CREATE TABLE positions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name)
);

-- Pre-populate with common positions
INSERT INTO positions (name, description) VALUES
('Manager', 'Manages a team or department'),
('Developer', 'Software developer or engineer'),
('Designer', 'UI/UX designer or graphic designer'),
('Sales', 'Sales representative or account manager'),
('HR', 'Human resources staff'),
('Accountant', 'Accounting and finance staff'),
('Worker', 'General worker or laborer'),
('Driver', 'Company driver'),
('Guard', 'Security guard or watchman'),
('Cleaner', 'Cleaning and maintenance staff');
```

#### B. Admin Bot Commands

**Add Position:**
```
/admin_add_position
Position Name: [Enter name]
Description: [Enter description]
```

**List Positions:**
```
/admin_list_positions

Active Positions:
1. Manager - Manages a team or department
2. Developer - Software developer or engineer
3. Designer - UI/UX designer or graphic designer
...

Use /admin_edit_position [id] to edit
Use /admin_deactivate_position [id] to deactivate
```

**Edit Position:**
```
/admin_edit_position 1
New Name: [Enter new name]
New Description: [Enter new description]
```

**Deactivate Position:**
```
/admin_deactivate_position 5
⚠️ This will hide the position from selection. Existing employees with this position will not be affected.

Confirm: [Yes] [No]
```

#### C. Integration with Employee Registration

In mini app, show dropdown of available positions:
```javascript
// Fetch positions from API
const positions = await fetch('/api/positions').then(r => r.json());

// Populate dropdown
const select = document.getElementById('position-select');
positions.forEach(pos => {
  const option = document.createElement('option');
  option.value = pos.name;
  option.textContent = `${pos.name} - ${pos.description}`;
  select.appendChild(option);
});
```

**API Endpoint:**
```python
# File: src/infrastructure/api/routes/position_routes.py

@app.route('/api/positions', methods=['GET'])
def get_positions():
    positions = position_repository.get_active_positions()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description
    } for p in positions])
```

---

### 2.3 Enable Other Features for Business

**Objective:** Activate or deactivate specific features for individual businesses based on their needs.

**Feature Flags System:**

#### A. Create Feature Flags Table

```sql
CREATE TABLE feature_flags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    feature_key VARCHAR(50) NOT NULL UNIQUE,
    feature_name VARCHAR(100) NOT NULL,
    description TEXT,
    default_enabled BOOLEAN DEFAULT FALSE,
    package_required VARCHAR(20),  -- minimum package level
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_key (feature_key)
);

CREATE TABLE group_feature_flags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    group_chat_id BIGINT NOT NULL,
    feature_key VARCHAR(50) NOT NULL,
    is_enabled BOOLEAN DEFAULT FALSE,
    enabled_at TIMESTAMP NULL,
    enabled_by BIGINT NULL,  -- admin user_id
    notes TEXT,
    FOREIGN KEY (group_chat_id) REFERENCES groups(chat_id) ON DELETE CASCADE,
    FOREIGN KEY (feature_key) REFERENCES feature_flags(feature_key) ON DELETE CASCADE,
    UNIQUE KEY unique_group_feature (group_chat_id, feature_key),
    INDEX idx_group (group_chat_id),
    INDEX idx_feature (feature_key)
);
```

#### B. Pre-defined Features

```sql
INSERT INTO feature_flags (feature_key, feature_name, description, default_enabled, package_required) VALUES
('check_in', 'Check-In System', 'GPS-based employee check-in', TRUE, 'free'),
('salary_advance', 'Salary Advances', 'Request and approve salary advances', FALSE, 'basic'),
('allowances', 'Allowances Management', 'Track transport, meal, and other allowances', FALSE, 'basic'),
('google_sheets', 'Google Sheets Export', 'Export reports to Google Sheets', FALSE, 'premium'),
('leave_management', 'Leave Management', 'Request and approve leave days', FALSE, 'basic'),
('overtime_tracking', 'Overtime Tracking', 'Track and calculate overtime hours', FALSE, 'premium'),
('performance_reviews', 'Performance Reviews', 'Conduct employee performance reviews', FALSE, 'premium'),
('payroll_automation', 'Payroll Automation', 'Automated monthly payroll calculation', FALSE, 'premium'),
('custom_reports', 'Custom Reports', 'Create custom report templates', FALSE, 'premium'),
('multi_location', 'Multi-Location Support', 'Support for businesses with multiple locations', FALSE, 'premium');
```

#### C. Admin Bot Commands

**List All Features:**
```
/admin_list_features

Available Features:
✅ check_in - Check-In System (Free)
✅ salary_advance - Salary Advances (Basic)
✅ allowances - Allowances Management (Basic)
✅ google_sheets - Google Sheets Export (Premium)
❌ leave_management - Leave Management (Basic) - BETA
❌ overtime_tracking - Overtime Tracking (Premium) - BETA
...
```

**Enable Feature for Group:**
```
/admin_enable_feature
Group: [Select from dropdown]
Feature: [Select from dropdown]
Notes: [Optional - reason for enabling]

Example:
Group: ABC Company
Feature: overtime_tracking
Notes: Requested by client, approved by manager
```

**Disable Feature for Group:**
```
/admin_disable_feature
Group: [Select from dropdown]
Feature: [Select from dropdown]
Reason: [Required - reason for disabling]
```

**Check Group Features:**
```
/admin_check_features
Group: [Enter chat_id or select from dropdown]

ABC Company (-1001234567890)
Package: Premium

Enabled Features:
✅ check_in
✅ salary_advance
✅ allowances
✅ google_sheets
✅ overtime_tracking

Available to Enable (Premium):
⬜ performance_reviews
⬜ custom_reports
⬜ multi_location
```

#### D. Feature Access Control in Code

```python
# File: src/application/use_cases/check_feature_access.py

class CheckFeatureAccessUseCase:
    def __init__(self, feature_repository, group_repository):
        self.feature_repository = feature_repository
        self.group_repository = group_repository

    def can_access_feature(self, group_chat_id: int, feature_key: str) -> tuple[bool, str]:
        """
        Check if a group can access a specific feature.
        Returns: (can_access, reason)
        """
        # Get group info
        group = self.group_repository.get_by_chat_id(group_chat_id)
        if not group:
            return False, "Group not found"

        # Get feature info
        feature = self.feature_repository.get_by_key(feature_key)
        if not feature:
            return False, "Feature not found"

        # Check if feature is globally enabled
        if not feature.default_enabled:
            # Check if specifically enabled for this group
            group_flag = self.feature_repository.get_group_feature_flag(
                group_chat_id, feature_key
            )
            if not group_flag or not group_flag.is_enabled:
                return False, "Feature not enabled for this group"

        # Check package requirements
        if feature.package_required:
            if not self._has_required_package(group.package_level, feature.package_required):
                return False, f"Requires {feature.package_required} package or higher"

        return True, "Access granted"

    def _has_required_package(self, current_package: str, required_package: str) -> bool:
        hierarchy = {'free': 1, 'basic': 2, 'premium': 3}
        return hierarchy.get(current_package, 0) >= hierarchy.get(required_package, 0)
```

**Usage in API Endpoints:**
```python
# File: src/infrastructure/api/routes/feature_gated_routes.py

@app.route('/api/overtime', methods=['POST'])
@require_telegram_auth
def submit_overtime():
    user = g.telegram_user
    group_chat_id = request.json.get('group_chat_id')

    # Check feature access
    can_access, reason = check_feature_access_use_case.can_access_feature(
        group_chat_id, 'overtime_tracking'
    )

    if not can_access:
        return jsonify({
            'error': 'Feature not available',
            'reason': reason,
            'upgrade_url': 'https://t.me/AutosumSupport'
        }), 403

    # Process overtime submission
    # ...
```

**Usage in Bot Commands:**
```python
# File: src/presentation/handlers/salary_advance_handler.py

async def salary_advance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # Check feature access
    can_access, reason = check_feature_access_use_case.can_access_feature(
        chat_id, 'salary_advance'
    )

    if not can_access:
        await update.message.reply_text(
            f"⛔ Salary advances are not available: {reason}\n\n"
            f"Contact @AutosumSupport to upgrade your package."
        )
        return

    # Continue with salary advance flow
    # ...
```

---

## 3. Technical Implementation Notes

### 3.1 Database Schema Changes Summary

**New Tables:**
```sql
-- 1. Positions management
CREATE TABLE positions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Feature flags
CREATE TABLE feature_flags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    feature_key VARCHAR(50) NOT NULL UNIQUE,
    feature_name VARCHAR(100) NOT NULL,
    description TEXT,
    default_enabled BOOLEAN DEFAULT FALSE,
    package_required VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Group-specific feature flags
CREATE TABLE group_feature_flags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    group_chat_id BIGINT NOT NULL,
    feature_key VARCHAR(50) NOT NULL,
    is_enabled BOOLEAN DEFAULT FALSE,
    enabled_at TIMESTAMP NULL,
    enabled_by BIGINT NULL,
    notes TEXT,
    FOREIGN KEY (group_chat_id) REFERENCES groups(chat_id),
    FOREIGN KEY (feature_key) REFERENCES feature_flags(feature_key),
    UNIQUE KEY unique_group_feature (group_chat_id, feature_key)
);
```

**Modify Existing Tables:**
```sql
-- Add package management to groups
ALTER TABLE groups
    ADD COLUMN package_level VARCHAR(20) DEFAULT 'free',
    ADD COLUMN package_updated_at TIMESTAMP NULL,
    ADD COLUMN package_updated_by BIGINT NULL;

-- Add business details to groups (optional)
ALTER TABLE groups
    ADD COLUMN business_name VARCHAR(255) NULL,
    ADD COLUMN industry VARCHAR(100) NULL,
    ADD COLUMN contact_phone VARCHAR(20) NULL,
    ADD COLUMN contact_email VARCHAR(255) NULL;
```

---

### 3.2 Mini App Deep Linking Implementation

**Bot-side: Generate Welcome Message with Deep Link**

```python
# File: src/presentation/handlers/group_join_handler.py

async def on_bot_added_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for when bot is added to a new group"""
    chat = update.effective_chat
    chat_id = chat.id
    group_name = chat.title

    # Register group in database
    group_repository.create_group(chat_id, group_name)

    # Generate deep link with group context
    bot_username = context.bot.username
    deep_link = f"https://t.me/{bot_username}/checkin?startapp=group_{abs(chat_id)}"

    # Send welcome message
    keyboard = [[InlineKeyboardButton("🚀 Open Mini App", url=deep_link)]]

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"👋 Welcome to OA Bot!\n\n"
             f"📌 **Quick Access for {group_name}:**\n"
             f"Tap the button below to open the mini app with this group pre-selected.\n\n"
             f"💡 **Tip:** Pin this message for easy access!\n\n"
             f"🔗 Direct link: {deep_link}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# Register handler in bot_app.py
application.add_handler(ChatMemberHandler(on_bot_added_to_group, ChatMemberHandler.MY_CHAT_MEMBER))
```

**Mini App-side: Parse Start Parameter**

```javascript
// File: mini-app/js/app.js (assumed location)

class OAMiniApp {
    constructor() {
        this.tg = window.Telegram.WebApp;
        this.tg.ready();
        this.selectedGroupId = null;
        this.userGroups = [];

        this.init();
    }

    async init() {
        // Parse start parameter
        const startParam = this.tg.initDataUnsafe?.start_param;

        if (startParam && startParam.startsWith('group_')) {
            // Extract group chat_id (remove 'group_' prefix and restore negative sign)
            const groupIdStr = startParam.replace('group_', '');
            this.selectedGroupId = `-${groupIdStr}`;

            console.log('Pre-selected group from deep link:', this.selectedGroupId);
        }

        // Fetch user's groups
        await this.loadUserGroups();

        // Pre-select group if available
        if (this.selectedGroupId) {
            this.selectGroup(this.selectedGroupId);
        }
    }

    async loadUserGroups() {
        try {
            const response = await fetch('/api/user/groups', {
                headers: {
                    'X-Telegram-Init-Data': this.tg.initData
                }
            });

            this.userGroups = await response.json();
            this.renderGroupSelector();
        } catch (error) {
            console.error('Failed to load groups:', error);
            this.tg.showAlert('Failed to load your groups. Please try again.');
        }
    }

    renderGroupSelector() {
        const selector = document.getElementById('group-selector');

        // If user has only one group, hide selector and auto-select
        if (this.userGroups.length === 1) {
            selector.style.display = 'none';
            this.selectGroup(this.userGroups[0].chat_id);
            return;
        }

        // Clear existing options
        selector.innerHTML = '<option value="">-- Select Group --</option>';

        // Add groups
        this.userGroups.forEach(group => {
            const option = document.createElement('option');
            option.value = group.chat_id;
            option.textContent = group.name;

            // Pre-select if matches deep link parameter
            if (group.chat_id === this.selectedGroupId) {
                option.selected = true;
            }

            selector.appendChild(option);
        });

        // Auto-select if pre-selected group exists
        if (this.selectedGroupId) {
            selector.value = this.selectedGroupId;
        }
    }

    selectGroup(groupChatId) {
        this.selectedGroupId = groupChatId;

        // Update UI
        document.getElementById('group-selector').value = groupChatId;

        // Load group-specific data
        this.loadGroupData(groupChatId);

        // Enable action buttons
        document.querySelectorAll('.group-action-btn').forEach(btn => {
            btn.disabled = false;
        });
    }

    async loadGroupData(groupChatId) {
        // Fetch employees, check-ins, etc. for this group
        // ...
    }

    async submitCheckIn(latitude, longitude, photo) {
        if (!this.selectedGroupId) {
            this.tg.showAlert('Please select a group first');
            return;
        }

        const formData = new FormData();
        formData.append('telegram_user_id', this.tg.initDataUnsafe.user.id);
        formData.append('group_chat_id', this.selectedGroupId);
        formData.append('latitude', latitude);
        formData.append('longitude', longitude);
        formData.append('photo', photo);

        try {
            const response = await fetch('/api/checkin', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Telegram-Init-Data': this.tg.initData
                }
            });

            if (response.ok) {
                this.tg.showAlert('Check-in successful!');
                this.tg.close();
            } else {
                const error = await response.json();
                this.tg.showAlert(`Error: ${error.message}`);
            }
        } catch (error) {
            console.error('Check-in failed:', error);
            this.tg.showAlert('Check-in failed. Please try again.');
        }
    }
}

// Initialize app
const app = new OAMiniApp();
```

**Backend: Add User Groups Endpoint**

```python
# File: src/infrastructure/api/routes/user_routes.py

@app.route('/api/user/groups', methods=['GET'])
@require_telegram_auth
def get_user_groups():
    """Get all groups the user belongs to"""
    telegram_user_id = g.telegram_user.telegram_id

    # Get employee record
    employee = employee_repository.get_by_telegram_id(telegram_user_id)
    if not employee:
        return jsonify([]), 200

    # Get all groups for this employee
    groups = employee_group_repository.get_groups_for_employee(employee.id)

    return jsonify([{
        'chat_id': g.chat_id,
        'name': g.name,
        'joined_at': g.joined_at.isoformat() if g.joined_at else None
    } for g in groups])
```

---

### 3.3 Admin Authentication

**Current State:**
- No admin authentication system
- Direct database access required for admin operations

**Proposed Implementation:**

```python
# File: src/infrastructure/config/settings.py

ADMIN_USER_IDS = [
    123456789,  # Admin 1 Telegram ID
    987654321,  # Admin 2 Telegram ID
]

# Or load from environment variable
import os
ADMIN_USER_IDS = [int(id) for id in os.getenv('ADMIN_USER_IDS', '').split(',') if id]
```

**Admin Middleware for Bot:**
```python
# File: src/presentation/handlers/admin_handler.py

def require_admin(func):
    """Decorator to restrict commands to admin users only"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id

        if user_id not in ADMIN_USER_IDS:
            await update.message.reply_text(
                "⛔ You are not authorized to use this command.\n"
                "This command is restricted to Autosum administrators."
            )
            return

        return await func(update, context)

    return wrapper

# Usage
@require_admin
async def update_package_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Admin-only logic
    pass
```

---

### 3.4 Migration Scripts

**Alembic Migration for Database Changes:**

```bash
# Generate new migration
alembic revision -m "add_package_management_and_features"
```

```python
# File: alembic/versions/XXXX_add_package_management_and_features.py

from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add package columns to groups
    op.add_column('groups', sa.Column('package_level', sa.String(20), server_default='free'))
    op.add_column('groups', sa.Column('package_updated_at', sa.TIMESTAMP, nullable=True))
    op.add_column('groups', sa.Column('package_updated_by', sa.BigInteger, nullable=True))
    op.add_column('groups', sa.Column('business_name', sa.String(255), nullable=True))
    op.add_column('groups', sa.Column('industry', sa.String(100), nullable=True))

    # Create positions table
    op.create_table(
        'positions',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.current_timestamp())
    )

    # Create feature_flags table
    op.create_table(
        'feature_flags',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('feature_key', sa.String(50), nullable=False, unique=True),
        sa.Column('feature_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('default_enabled', sa.Boolean, default=False),
        sa.Column('package_required', sa.String(20), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.current_timestamp())
    )

    # Create group_feature_flags table
    op.create_table(
        'group_feature_flags',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('group_chat_id', sa.BigInteger, nullable=False),
        sa.Column('feature_key', sa.String(50), nullable=False),
        sa.Column('is_enabled', sa.Boolean, default=False),
        sa.Column('enabled_at', sa.TIMESTAMP, nullable=True),
        sa.Column('enabled_by', sa.BigInteger, nullable=True),
        sa.Column('notes', sa.Text, nullable=True)
    )

    # Add foreign keys
    op.create_foreign_key(
        'fk_group_feature_flags_group',
        'group_feature_flags', 'groups',
        ['group_chat_id'], ['chat_id'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'fk_group_feature_flags_feature',
        'group_feature_flags', 'feature_flags',
        ['feature_key'], ['feature_key'],
        ondelete='CASCADE'
    )

    # Add unique constraint
    op.create_unique_constraint(
        'uq_group_feature',
        'group_feature_flags',
        ['group_chat_id', 'feature_key']
    )

    # Insert default positions
    op.execute("""
        INSERT INTO positions (name, description) VALUES
        ('Manager', 'Manages a team or department'),
        ('Developer', 'Software developer or engineer'),
        ('Designer', 'UI/UX designer or graphic designer'),
        ('Sales', 'Sales representative or account manager'),
        ('Worker', 'General worker or laborer'),
        ('Driver', 'Company driver'),
        ('Guard', 'Security guard'),
        ('Cleaner', 'Cleaning staff')
    """)

    # Insert default feature flags
    op.execute("""
        INSERT INTO feature_flags (feature_key, feature_name, description, default_enabled, package_required) VALUES
        ('check_in', 'Check-In System', 'GPS-based employee check-in', TRUE, 'free'),
        ('salary_advance', 'Salary Advances', 'Request and approve salary advances', TRUE, 'basic'),
        ('allowances', 'Allowances Management', 'Track various allowances', TRUE, 'basic'),
        ('google_sheets', 'Google Sheets Export', 'Export reports to Google Sheets', FALSE, 'premium'),
        ('leave_management', 'Leave Management', 'Request and approve leave', FALSE, 'basic'),
        ('overtime_tracking', 'Overtime Tracking', 'Track overtime hours', FALSE, 'premium')
    """)

def downgrade():
    op.drop_constraint('fk_group_feature_flags_feature', 'group_feature_flags', type_='foreignkey')
    op.drop_constraint('fk_group_feature_flags_group', 'group_feature_flags', type_='foreignkey')
    op.drop_constraint('uq_group_feature', 'group_feature_flags', type_='unique')

    op.drop_table('group_feature_flags')
    op.drop_table('feature_flags')
    op.drop_table('positions')

    op.drop_column('groups', 'industry')
    op.drop_column('groups', 'business_name')
    op.drop_column('groups', 'package_updated_by')
    op.drop_column('groups', 'package_updated_at')
    op.drop_column('groups', 'package_level')
```

---

## 4. API Documentation

### 4.1 Existing Endpoints

**Base URL:** `http://localhost:80/api`

**Authentication:** All endpoints require `X-Telegram-Init-Data` header with Telegram Web App signature.

#### POST /api/checkin
Submit employee check-in with location and photo.

**Request:**
```
Content-Type: multipart/form-data

telegram_user_id: 123456789
group_chat_id: -1001234567890
group_name: ABC Company
latitude: 11.5564
longitude: 104.9282
photo: [file]
```

**Response:**
```json
{
  "success": true,
  "message": "Check-in recorded successfully",
  "check_in_id": 42
}
```

---

### 4.2 Proposed New Endpoints

#### GET /api/user/groups
Get all groups the authenticated user belongs to.

**Response:**
```json
[
  {
    "chat_id": "-1001234567890",
    "name": "ABC Company",
    "joined_at": "2025-01-15T08:30:00Z"
  },
  {
    "chat_id": "-1009876543210",
    "name": "XYZ Corporation",
    "joined_at": "2025-02-01T09:00:00Z"
  }
]
```

---

#### GET /api/positions
Get all active positions/roles.

**Response:**
```json
[
  {
    "id": 1,
    "name": "Manager",
    "description": "Manages a team or department"
  },
  {
    "id": 2,
    "name": "Developer",
    "description": "Software developer or engineer"
  }
]
```

---

#### GET /api/group/{chat_id}/features
Get enabled features for a specific group.

**Response:**
```json
{
  "group": {
    "chat_id": "-1001234567890",
    "name": "ABC Company",
    "package_level": "premium"
  },
  "features": [
    {
      "key": "check_in",
      "name": "Check-In System",
      "enabled": true
    },
    {
      "key": "salary_advance",
      "name": "Salary Advances",
      "enabled": true
    },
    {
      "key": "google_sheets",
      "name": "Google Sheets Export",
      "enabled": true
    }
  ]
}
```

---

## 5. Bot Commands Reference

### 5.1 User Commands

| Command | Description | Availability |
|---------|-------------|--------------|
| /start | Start conversation with bot, show main menu | All users |
| /checkin | Initiate check-in process (redirects to mini app) | Registered employees |
| /balance | View salary balance and advances | Registered employees |
| /help | Show help message | All users |

---

### 5.2 Admin Commands (Proposed)

| Command | Description | Requires |
|---------|-------------|----------|
| /admin_update_package | Update package for a group | Admin role |
| /admin_add_position | Add new position/role | Admin role |
| /admin_list_positions | List all positions | Admin role |
| /admin_edit_position | Edit position details | Admin role |
| /admin_deactivate_position | Deactivate position | Admin role |
| /admin_list_features | List all feature flags | Admin role |
| /admin_enable_feature | Enable feature for group | Admin role |
| /admin_disable_feature | Disable feature for group | Admin role |
| /admin_check_features | Check enabled features for group | Admin role |
| /admin_stats | View system statistics | Admin role |

---

## 6. Development Roadmap

### Phase 1: Foundation (Current State)
- ✅ Basic bot with check-in functionality
- ✅ Telegram Web App integration
- ✅ Employee and group management
- ✅ Salary advances and allowances tracking
- ✅ Google Sheets export (basic)

### Phase 2: Package Management (High Priority)
- [ ] Add package_level column to groups table
- [ ] Implement package update bot commands for admins
- [ ] Create feature access control logic
- [ ] Add package upgrade prompts in mini app
- [ ] Design package pricing and payment flow

### Phase 3: Position Management (High Priority)
- [ ] Create positions table and API
- [ ] Add position management admin commands
- [ ] Integrate position dropdown in employee registration
- [ ] Migrate existing free-text roles to positions

### Phase 4: Feature Flags System (Medium Priority)
- [ ] Create feature_flags and group_feature_flags tables
- [ ] Implement admin commands for feature management
- [ ] Add feature access checks to all relevant endpoints
- [ ] Display available features in mini app settings

### Phase 5: Mini App Deep Linking (High Priority)
- [ ] Implement welcome message with group-specific deep links
- [ ] Add start parameter parsing in mini app
- [ ] Test deep linking across multiple groups
- [ ] Add pin message reminder for admins

### Phase 6: Advanced Features (Low Priority)
- [ ] Leave management system
- [ ] Overtime tracking
- [ ] Performance reviews
- [ ] Custom report builder
- [ ] Multi-location support
- [ ] Payroll automation

### Phase 7: Business Analytics (Medium Priority)
- [ ] Dashboard for business admins
- [ ] Real-time attendance analytics
- [ ] Salary expense forecasting
- [ ] Employee performance metrics
- [ ] Export to accounting software (QuickBooks, Xero)

---

## 7. Security Considerations

### 7.1 Authentication & Authorization
- ✅ Telegram Web App signature verification (HMAC-SHA256)
- ✅ Rate limiting: 20 requests/minute per user
- ✅ Cache TTL: 5 minutes
- [ ] Admin role verification for sensitive commands
- [ ] Group admin verification for business operations
- [ ] API key authentication for external integrations

### 7.2 Data Protection
- ✅ Environment variables for sensitive config (.env)
- [ ] Encrypt salary data at rest
- [ ] PII anonymization in logs
- [ ] GDPR compliance (right to be forgotten)
- [ ] Regular database backups

### 7.3 Input Validation
- ✅ Telegram initData validation
- ✅ File upload size limits (16MB)
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention in mini app
- [ ] CSRF protection for API endpoints

---

## 8. Testing Strategy

### 8.1 Unit Tests
- Repository layer tests (CRUD operations)
- Use case tests (business logic)
- Utility function tests (validation, formatting)

### 8.2 Integration Tests
- Bot command handlers
- API endpoint tests
- Database migration tests
- Telegram Web App authentication flow

### 8.3 E2E Tests
- Full check-in flow (bot → mini app → API → database)
- Employee registration and approval
- Package upgrade and feature enablement
- Multi-group user workflow

### 8.4 Manual Testing Checklist
- [ ] Bot responds to all commands in group chat
- [ ] Bot responds to all commands in private chat
- [ ] Mini app loads correctly from bot menu
- [ ] Deep link with group parameter pre-selects group
- [ ] Check-in captures photo and location correctly
- [ ] Admin commands work only for authorized users
- [ ] Package-restricted features are properly gated
- [ ] Google Sheets export generates correct data

---

## 9. Deployment Notes

### 9.1 Current Setup
- **Python Version:** 3.13
- **Server:** Running on port 80 (Flask API)
- **Bot Mode:** Polling (not webhook)
- **Services:** 3 concurrent processes (check-in bot, balance bot, API server)

### 9.2 Environment Variables Required
```bash
# Telegram Bot
BOT_TOKEN=your_bot_token_here
BOT_USERNAME=OALocal_bot

# Database
DB_HOST=localhost
DB_PORT=3306
DB_NAME=office_automation
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# API
API_PORT=80
SECRET_KEY=your_flask_secret_key

# Admin Users (comma-separated Telegram user IDs)
ADMIN_USER_IDS=123456789,987654321

# Google Sheets (if using export feature)
GOOGLE_SHEETS_CREDENTIALS_PATH=/path/to/credentials.json
```

### 9.3 Deployment Steps
1. Set up MySQL database
2. Run Alembic migrations: `alembic upgrade head`
3. Configure environment variables
4. Install dependencies: `pip install -r requirements.txt`
5. Start services: `python main.py`
6. Verify bot is running: Send /start to bot
7. Test mini app: Open from bot menu

---

## 10. Support & Maintenance

### 10.1 User Support Channels
- **Telegram:** @AutosumSupport
- **Email:** support@autosum.com
- **Documentation:** https://docs.autosum.com/oa-bot

### 10.2 Monitoring
- Bot uptime monitoring
- API response time tracking
- Database performance metrics
- Error rate alerts (Sentry or similar)

### 10.3 Backup Strategy
- Daily database backups
- Weekly full system snapshots
- Monthly audit logs archive

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| OA Bot | Office Automation Bot - The main Telegram bot for employee management |
| Mini App | Telegram Web App embedded within Telegram messenger |
| Check-In | Employee location-based attendance recording with photo |
| Salary Advance | Early payment of salary before the regular payday |
| Allowance | Additional payments (transport, meal, overtime, etc.) |
| Package | Subscription tier (Free, Basic, Premium) |
| Feature Flag | System to enable/disable specific features per group |
| Deep Link | URL that opens a specific part of the app with context |
| Start Parameter | Query parameter passed to mini app on launch |
| Group | Telegram group chat representing a business/organization |

---

## Appendix B: File Structure Reference

```
office-automation/
├── main.py                          # Entry point (multiprocessing)
├── requirements.txt                 # Python dependencies
├── .env                            # Environment variables (not in repo)
├── .env.example                    # Example env file
├── alembic/                        # Database migrations
│   └── versions/                   # Migration scripts
├── src/
│   ├── domain/                     # Business entities & interfaces
│   │   ├── entities/
│   │   │   ├── employee.py
│   │   │   ├── group.py
│   │   │   ├── check_in.py
│   │   │   └── employee_group.py
│   │   └── repositories/           # Repository interfaces
│   ├── application/                # Use cases & business logic
│   │   ├── use_cases/
│   │   │   ├── register_employee.py
│   │   │   ├── record_check_in.py
│   │   │   └── check_feature_access.py  # [TO ADD]
│   │   └── dto/                    # Data transfer objects
│   ├── infrastructure/             # External services & implementations
│   │   ├── telegram/
│   │   │   ├── bot_app.py         # Main bot application
│   │   │   └── balance_bot_app.py # Balance summary bot
│   │   ├── api/
│   │   │   ├── flask_app.py       # Flask app initialization
│   │   │   ├── routes/
│   │   │   │   ├── checkin_routes.py
│   │   │   │   ├── user_routes.py      # [TO ADD]
│   │   │   │   └── position_routes.py  # [TO ADD]
│   │   │   └── middleware/
│   │   │       └── telegram_auth.py
│   │   ├── persistence/
│   │   │   ├── models.py          # SQLAlchemy models
│   │   │   └── repositories/      # Repository implementations
│   │   └── config/
│   │       └── settings.py        # Configuration management
│   └── presentation/               # Telegram handlers
│       └── handlers/
│           ├── check_in_handler.py
│           ├── admin_handler.py   # [TO ADD]
│           └── group_join_handler.py  # [TO ADD]
└── EMPLOYEE_MANAGEMENT_BLUEPRINT.md  # This document
```

---

## Appendix C: Quick Start for Developers

### Set Up Development Environment
```bash
# Clone repository
git clone <repo_url>
cd office-automation

# Create virtual environment
python3.13 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your credentials

# Run database migrations
alembic upgrade head

# Start application
python main.py
```

### Test Bot Locally
1. Message your bot on Telegram: /start
2. Add bot to a test group
3. Try check-in: Click "Check In" button
4. Verify mini app opens correctly

### Run Migrations
```bash
# Create new migration
alembic revision -m "description_of_changes"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# Show current version
alembic current
```

---

## Document Version
- **Version:** 1.0
- **Last Updated:** 2025-11-19
- **Author:** Claude (Autosum Team)
- **Status:** Draft for Review

---

**End of Blueprint**