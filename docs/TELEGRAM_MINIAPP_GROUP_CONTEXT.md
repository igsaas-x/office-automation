# Telegram Mini App Group Context Solution

## Problem Statement

### Business Requirement

The office automation system needs customers to:
1. Register Telegram groups that map to businesses
2. Add employees to the group
3. Have employees use a Telegram miniapp to check in
4. Automatically track which business/group each check-in belongs to
5. Generate reports per group/business

### Technical Challenge

**The Problem:**
When an employee opens a Telegram miniapp, there is no inherent context of which group/business they belong to. The miniapp needs to automatically know which group the employee is checking in for.

**Why This Matters:**
- The system needs to know which business to attribute the check-in to
- Reports need to be generated per business/group
- Without group context, the system cannot differentiate between businesses
- Manual group selection creates friction and potential errors

**Example Scenario:**
```
ABC Company (Group ID: -1001234567890)
- Has 20 employees in the Telegram group
- When employee John opens the miniapp to check in:
  ❌ Problem: Miniapp doesn't know it's for ABC Company
  ✅ Solution: Deep link with group context automatically selects ABC Company
```

---

## Solution Architecture

### Overview

We will implement a **simple deep link approach** with:
1. **Group Registration** - Admin registers the group via `/register` command
2. **Menu Command** - Employees use `/menu` command in group to access miniapp
3. **Deep Links** - Inline buttons with group context automatically select the business
4. **User-Group Mapping** - Backend tracks which employees belong to which groups

### Flow Diagram

```
SOLUTION FLOW
═══════════════════════════════════════════════════════════════

PHASE 1: GROUP SETUP (Business Admin - One Time)
┌─────────────────────────────────────────────────────────────┐
│  1. Business admin creates Telegram group                   │
│  2. Adds @OALocal_bot to the group                          │
│  3. Adds all employees to the group                         │
│  4. Runs /register command                                  │
│  5. Bot registers group and generates deep link             │
│     (stored internally, used by /menu command)              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
PHASE 2: EMPLOYEE DAILY USAGE
┌─────────────────────────────────────────────────────────────┐
│  1. Employee opens the Telegram group                       │
│  2. Runs /menu command (or clicks bot menu button)          │
│  3. Bot shows inline keyboard with buttons:                 │
│     [✅ Check In] [💰 View Balance] [📊 Reports]            │
│  4. Employee clicks "Check In" button                       │
│  5. Miniapp opens with automatic group selection            │
│     → Deep link: t.me/bot/checkin?startapp=group_12345      │
│  6. Employee takes photo, submits check-in                  │
│  7. Backend automatically associates check-in with group    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
RESULT: All check-ins automatically tagged with correct business
```

---

## Detailed Solution

### 1. Deep Linking via `/menu` Command

**How It Works:**
1. Employees are added to the Telegram group by the admin
2. Employees run `/menu` command in the group
3. Bot responds with inline keyboard buttons
4. Each button is a deep link with group context embedded

**Deep Link Format:**
```
https://t.me/{bot_username}/{app_short_name}?startapp=group_{group_chat_id}
```

**Example:**
```
https://t.me/OALocal_bot/checkin?startapp=group_1001234567890
```

When the button is clicked:
- The miniapp receives `start_param = "group_1001234567890"`
- The miniapp parses this to extract the group ID
- The group is automatically selected
- No manual selection needed

**Benefits:**
- ✅ Zero user friction - automatic group selection
- ✅ Always accessible - just run `/menu` in the group
- ✅ No link management - employees don't need to save links
- ✅ Self-service - no need to contact admin for link
- ✅ Scalable - works for multiple action buttons

---

### 2. Backend User-Group Mapping

**Database Schema:**

```sql
-- Many-to-many relationship: users can belong to multiple groups
CREATE TABLE employee_groups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    group_chat_id BIGINT NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (group_chat_id) REFERENCES groups(chat_id) ON DELETE CASCADE,
    UNIQUE KEY unique_employee_group (employee_id, group_chat_id),
    INDEX idx_employee (employee_id),
    INDEX idx_group (group_chat_id)
);
```

**How It Works:**
1. When an employee first checks in via a deep link, the system creates a mapping
2. The mapping links the employee's Telegram user ID to the group
3. On subsequent visits, the system can look up which group(s) the employee belongs to

**Example Data:**
```
employee_id | group_chat_id      | joined_at          | is_active
------------|--------------------|--------------------|----------
1           | -1001234567890     | 2025-01-15 08:00   | TRUE
1           | -1009876543210     | 2025-02-01 09:00   | TRUE
2           | -1001234567890     | 2025-01-20 10:00   | TRUE
```

Employee #1 belongs to 2 groups, Employee #2 belongs to 1 group.

---

### 3. Group Selection Logic in Mini App

**Decision Tree:**

```
User opens miniapp
    │
    └─→ Has startapp parameter with group_id?
        │
        ├─→ YES: Auto-select that group ✅
        │        (This is the normal flow via /menu command)
        │
        └─→ NO: Show error message ⚠️
                "Please open this app from your business group using /menu command"
```

**User Experience:**

| Scenario | User Action | Miniapp Behavior |
|----------|-------------|------------------|
| Normal flow | Run `/menu` in group → Click "Check In" | ✅ Auto-selects group, no interaction needed |
| Direct open (not recommended) | Opens miniapp from bot chat | ⚠️ Shows "Please use /menu in your group" |

**Why This is Simple:**
- Only ONE way to open the miniapp: via `/menu` command in group
- Group context is ALWAYS present via deep link parameter
- No complex multi-group selection logic needed
- Clear error message if opened incorrectly

---

## Technical Implementation

### Step 1: Bot - Register Group Command

**File:** `src/presentation/handlers/registration_handler.py`

This command registers the group and sets up the bot. Employees will use `/menu` command to access the miniapp.

```python
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

WAITING_FOR_BUSINESS_NAME = 1

async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /register command in group"""
    chat = update.effective_chat

    # Only works in group chats
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text(
            "⛔ This command only works in group chats.\n\n"
            "Please add me to your business group and run this command there."
        )
        return ConversationHandler.END

    # Check if already registered
    from src.infrastructure.persistence.repositories.group_repository import GroupRepository
    group_repo = GroupRepository()
    existing = group_repo.get_by_chat_id(chat.id)

    if existing:
        bot_username = context.bot.username
        deep_link = f"https://t.me/{bot_username}/checkin?startapp=group_{abs(chat.id)}"

        await update.message.reply_text(
            f"✅ This group is already registered!\n\n"
            f"**Business Name:** {existing.business_name}\n"
            f"**Package:** {existing.package_level.title()}\n\n"
            f"🔗 **Employee Access Link:**\n{deep_link}\n\n"
            f"📌 Share this link with your employees for easy access!",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    # Prompt for business name
    await update.message.reply_text(
        "📝 **Register Your Business**\n\n"
        "Please enter your business or branch name:",
        parse_mode='Markdown'
    )

    return WAITING_FOR_BUSINESS_NAME


async def receive_business_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and save business name, then generate deep link"""
    business_name = update.message.text.strip()
    chat = update.effective_chat

    # Validate business name
    if len(business_name) < 3:
        await update.message.reply_text(
            "⚠️ Business name must be at least 3 characters.\n"
            "Please try again:"
        )
        return WAITING_FOR_BUSINESS_NAME

    # Save to database
    from src.infrastructure.persistence.repositories.group_repository import GroupRepository
    group_repo = GroupRepository()

    group = group_repo.create_group(
        chat_id=chat.id,
        name=chat.title,
        business_name=business_name,
        package_level='free'
    )

    # Generate deep link with group context
    bot_username = context.bot.username
    deep_link = f"https://t.me/{bot_username}/checkin?startapp=group_{abs(chat.id)}"

    # Create button
    keyboard = [[InlineKeyboardButton("🚀 Open Mini App", url=deep_link)]]

    await update.message.reply_text(
        f"✅ **Registration Successful!**\n\n"
        f"**Business Name:** {business_name}\n"
        f"**Group ID:** `{chat.id}`\n"
        f"**Package:** Free (contact @AutosumSupport to upgrade)\n\n"
        f"📋 **Next Steps:**\n"
        f"1. Add all employees to this Telegram group\n"
        f"2. Employees can use /menu command to access check-in and other features\n"
        f"3. All check-ins will automatically be associated with {business_name}\n\n"
        f"💡 **Tip:** Try the /menu command now to see available actions!",
        parse_mode='Markdown'
    )

    return ConversationHandler.END
```

---

### Step 2: Bot - Menu Command with Deep Links

**File:** `src/presentation/handlers/menu_handler.py`

This is the PRIMARY way employees access the miniapp.

```python
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show menu with action buttons (Check In, Balance, Reports, etc.)
    Each button is a deep link with group context embedded.
    """
    chat = update.effective_chat

    # Only works in group chats (where employees are members)
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text(
            "⚠️ This command only works in group chats.\n\n"
            "Please use this command in your business group to access the menu."
        )
        return

    # Get group info
    from src.infrastructure.persistence.repositories.group_repository import GroupRepository
    group_repo = GroupRepository()
    group = group_repo.get_by_chat_id(chat.id)

    if not group:
        await update.message.reply_text(
            "⚠️ This group is not registered.\n\n"
            "Please ask an admin to run /register first to set up this business."
        )
        return

    # Generate deep links with group context
    bot_username = context.bot.username
    group_id_param = abs(chat.id)  # Remove negative sign for URL

    checkin_link = f"https://t.me/{bot_username}/checkin?startapp=group_{group_id_param}"
    balance_link = f"https://t.me/{bot_username}/balance?startapp=group_{group_id_param}"
    reports_link = f"https://t.me/{bot_username}/reports?startapp=group_{group_id_param}"

    # Create inline keyboard with action buttons
    keyboard = [
        [InlineKeyboardButton("✅ Check In", url=checkin_link)],
        [InlineKeyboardButton("💰 View Balance", url=balance_link)],
        [InlineKeyboardButton("📊 My Reports", url=reports_link)],
    ]

    await update.message.reply_text(
        f"**{group.business_name}**\n\n"
        f"Select an action below:\n"
        f"• **Check In** - Record your attendance with photo & location\n"
        f"• **View Balance** - See your salary balance and advances\n"
        f"• **My Reports** - View your attendance and payment history",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


# Register the handler in bot initialization
# In src/infrastructure/telegram/bot_app.py

from telegram.ext import CommandHandler
from src.presentation.handlers.menu_handler import menu_command
from src.presentation.handlers.registration_handler import (
    register_command,
    receive_business_name,
    WAITING_FOR_BUSINESS_NAME
)

# Registration conversation handler
registration_conv = ConversationHandler(
    entry_points=[CommandHandler('register', register_command)],
    states={
        WAITING_FOR_BUSINESS_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_business_name)
        ],
    },
    fallbacks=[],
)

# Add handlers
application.add_handler(registration_conv)
application.add_handler(CommandHandler('menu', menu_command))
```

---

### Step 3: Mini App - Parse Start Parameter

**File:** `mini-app/js/app.js` (or your miniapp JavaScript)

```javascript
/**
 * Main Mini App Class
 */
class OAMiniApp {
    constructor() {
        this.tg = window.Telegram.WebApp;
        this.tg.ready();

        this.selectedGroupId = null;
        this.userGroups = [];

        this.init();
    }

    async init() {
        console.log('Initializing OA Mini App...');

        // Parse start parameter from deep link
        const startParam = this.tg.initDataUnsafe?.start_param;

        if (startParam) {
            console.log('Start parameter detected:', startParam);

            if (startParam.startsWith('group_')) {
                // Extract group chat_id
                // Format: "group_1001234567890" (without negative sign)
                const groupIdStr = startParam.replace('group_', '');

                // Restore negative sign (Telegram group IDs are negative)
                this.selectedGroupId = `-${groupIdStr}`;

                console.log('Pre-selected group from deep link:', this.selectedGroupId);
            }
        }

        // Load user's groups from backend
        await this.loadUserGroups();

        // Handle group selection
        this.handleGroupSelection();

        // Initialize UI
        this.initializeUI();
    }

    handleGroupSelection() {
        // SIMPLIFIED: We expect group_id from deep link ALWAYS
        // (because users should only open via /menu command)

        if (!this.selectedGroupId) {
            // User opened miniapp incorrectly (not via /menu command)
            this.showIncorrectAccessMessage();
            return;
        }

        // Group is already selected from deep link
        console.log('Group auto-selected:', this.selectedGroupId);
        this.loadGroupData();
        this.enableActionButtons();
    }

    showIncorrectAccessMessage() {
        const container = document.getElementById('app-container');
        container.innerHTML = `
            <div class="incorrect-access-message">
                <h2>⚠️ Incorrect Access</h2>
                <p>Please open this app from your business Telegram group.</p>
                <p><strong>How to access:</strong></p>
                <ol>
                    <li>Open your business Telegram group</li>
                    <li>Run the <code>/menu</code> command</li>
                    <li>Click the "Check In" button</li>
                </ol>
                <p>This ensures your check-in is associated with the correct business.</p>
            </div>
        `;

        // Disable all action buttons
        document.querySelectorAll('.group-action-btn').forEach(btn => {
            btn.disabled = true;
        });
    }

    async loadGroupData() {
        if (!this.selectedGroupId) return;

        // Load group name to display
        try {
            const response = await fetch(`/api/groups/${this.selectedGroupId}`, {
                headers: {
                    'X-Telegram-Init-Data': this.tg.initData
                }
            });

            if (response.ok) {
                const group = await response.json();
                this.displayGroupName(group.business_name);
            }
        } catch (error) {
            console.error('Error loading group data:', error);
        }
    }

    displayGroupName(businessName) {
        const groupNameDisplay = document.getElementById('business-name');
        if (groupNameDisplay) {
            groupNameDisplay.textContent = businessName;
        }
    }

    enableActionButtons() {
        document.querySelectorAll('.group-action-btn').forEach(btn => {
            btn.disabled = false;
        });
    }

    initializeUI() {
        // Initialize your UI components
        // Set up event listeners, etc.

        this.setupCheckInButton();
    }

    setupCheckInButton() {
        const checkInBtn = document.getElementById('check-in-btn');
        if (checkInBtn) {
            checkInBtn.addEventListener('click', () => this.handleCheckIn());
        }
    }

    async handleCheckIn() {
        if (!this.selectedGroupId) {
            this.tg.showAlert('Please select a business first');
            return;
        }

        // Request location and photo permissions
        // Implementation details depend on your check-in flow

        console.log('Starting check-in for group:', this.selectedGroupId);

        // Example: Capture location
        if (!navigator.geolocation) {
            this.tg.showAlert('Geolocation is not supported by your device');
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => this.capturePhoto(position),
            (error) => {
                console.error('Geolocation error:', error);
                this.tg.showAlert('Unable to get your location. Please enable location services.');
            }
        );
    }

    async capturePhoto(position) {
        // Implement photo capture
        // This is a simplified example

        const photoInput = document.createElement('input');
        photoInput.type = 'file';
        photoInput.accept = 'image/*';
        photoInput.capture = 'environment';

        photoInput.onchange = async (e) => {
            const file = e.target.files[0];
            if (file) {
                await this.submitCheckIn(
                    position.coords.latitude,
                    position.coords.longitude,
                    file
                );
            }
        };

        photoInput.click();
    }

    async submitCheckIn(latitude, longitude, photoFile) {
        const formData = new FormData();
        formData.append('telegram_user_id', this.tg.initDataUnsafe.user.id);
        formData.append('group_chat_id', this.selectedGroupId);
        formData.append('latitude', latitude);
        formData.append('longitude', longitude);
        formData.append('photo', photoFile);

        try {
            const response = await fetch('/api/checkin', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Telegram-Init-Data': this.tg.initData
                }
            });

            if (response.ok) {
                const result = await response.json();
                this.tg.showAlert('✅ Check-in successful!');

                // Optionally close the mini app
                setTimeout(() => this.tg.close(), 1500);
            } else {
                const error = await response.json();
                this.tg.showAlert(`❌ Error: ${error.message || 'Check-in failed'}`);
            }
        } catch (error) {
            console.error('Check-in submission error:', error);
            this.tg.showAlert('❌ Network error. Please try again.');
        }
    }
}

// Initialize the app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.oaApp = new OAMiniApp();
    });
} else {
    window.oaApp = new OAMiniApp();
}
```

---

### Step 4: Backend API - Get Group Info

**File:** `src/infrastructure/api/routes/group_routes.py`

Simple endpoint to get group information for display.

```python
from flask import Blueprint, jsonify, g
from src.infrastructure.api.middleware.telegram_auth import require_telegram_auth
from src.infrastructure.persistence.repositories.group_repository import GroupRepository

group_bp = Blueprint('groups', __name__, url_prefix='/api/groups')

group_repo = GroupRepository()


@group_bp.route('/<group_chat_id>', methods=['GET'])
@require_telegram_auth
def get_group_info(group_chat_id):
    """
    Get group/business information.

    Args:
        group_chat_id: The Telegram group chat ID

    Returns:
        Group details including business name
    """
    group = group_repo.get_by_chat_id(int(group_chat_id))

    if not group:
        return jsonify({'error': 'Group not found'}), 404

    return jsonify({
        'chat_id': str(group.chat_id),
        'name': group.name,
        'business_name': group.business_name,
        'package_level': group.package_level
    }), 200
```

**Register the blueprint in Flask app:**

```python
# In src/infrastructure/api/flask_app.py

from src.infrastructure.api.routes.group_routes import group_bp

app.register_blueprint(group_bp)
```

---

### Step 5: Repository Implementation

**File:** `src/infrastructure/persistence/repositories/employee_group_repository.py`

```python
from typing import List, Optional
from sqlalchemy import and_
from src.infrastructure.persistence.database import get_session
from src.infrastructure.persistence.models import EmployeeGroup, Employee, Group


class EmployeeGroupRepository:
    """Repository for managing employee-group associations"""

    def create_association(
        self,
        employee_id: int,
        group_chat_id: int
    ) -> EmployeeGroup:
        """
        Create an association between an employee and a group.
        If association already exists, return it.
        """
        session = get_session()

        # Check if association already exists
        existing = session.query(EmployeeGroup).filter(
            and_(
                EmployeeGroup.employee_id == employee_id,
                EmployeeGroup.group_chat_id == group_chat_id
            )
        ).first()

        if existing:
            return existing

        # Create new association
        association = EmployeeGroup(
            employee_id=employee_id,
            group_chat_id=group_chat_id,
            is_active=True
        )

        session.add(association)
        session.commit()
        session.refresh(association)

        return association

    def get_groups_for_employee(self, employee_id: int) -> List[Group]:
        """
        Get all groups that an employee belongs to.
        """
        session = get_session()

        groups = session.query(Group).join(
            EmployeeGroup,
            Group.chat_id == EmployeeGroup.group_chat_id
        ).filter(
            and_(
                EmployeeGroup.employee_id == employee_id,
                EmployeeGroup.is_active == True
            )
        ).all()

        return groups

    def get_employees_for_group(self, group_chat_id: int) -> List[Employee]:
        """
        Get all employees that belong to a group.
        """
        session = get_session()

        employees = session.query(Employee).join(
            EmployeeGroup,
            Employee.id == EmployeeGroup.employee_id
        ).filter(
            and_(
                EmployeeGroup.group_chat_id == group_chat_id,
                EmployeeGroup.is_active == True
            )
        ).all()

        return employees

    def remove_association(
        self,
        employee_id: int,
        group_chat_id: int
    ) -> bool:
        """
        Soft delete: Mark association as inactive.
        """
        session = get_session()

        association = session.query(EmployeeGroup).filter(
            and_(
                EmployeeGroup.employee_id == employee_id,
                EmployeeGroup.group_chat_id == group_chat_id
            )
        ).first()

        if not association:
            return False

        association.is_active = False
        session.commit()

        return True
```

---

### Step 6: Update Check-In Endpoint to Auto-Create Mapping

**File:** `src/infrastructure/api/routes/checkin_routes.py`

```python
from flask import request, jsonify
from src.infrastructure.api.middleware.telegram_auth import require_telegram_auth
from src.infrastructure.persistence.repositories.employee_repository import EmployeeRepository
from src.infrastructure.persistence.repositories.employee_group_repository import EmployeeGroupRepository
from src.infrastructure.persistence.repositories.checkin_repository import CheckInRepository

employee_repo = EmployeeRepository()
employee_group_repo = EmployeeGroupRepository()
checkin_repo = CheckInRepository()


@app.route('/api/checkin', methods=['POST'])
@require_telegram_auth
def submit_checkin():
    """
    Submit a check-in with photo and location.
    Auto-creates employee-group association if first check-in.
    """
    telegram_user_id = g.telegram_user_id

    # Get form data
    group_chat_id = request.form.get('group_chat_id')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    photo = request.files.get('photo')

    # Validation
    if not all([group_chat_id, latitude, longitude, photo]):
        return jsonify({'error': 'Missing required fields'}), 400

    # Find or create employee
    employee = employee_repo.get_by_telegram_id(telegram_user_id)

    if not employee:
        # First time user - create employee record
        # You might want to collect name, phone, etc. in a separate registration flow
        employee = employee_repo.create_employee(
            telegram_id=telegram_user_id,
            telegram_username=g.telegram_user.username,
            name=f"{g.telegram_user.first_name} {g.telegram_user.last_name or ''}".strip(),
            # Other fields can be updated later
        )

    # Create employee-group association (if doesn't exist)
    employee_group_repo.create_association(
        employee_id=employee.id,
        group_chat_id=int(group_chat_id)
    )

    # Save photo and create check-in record
    photo_path = save_photo(photo)  # Implement your photo saving logic

    checkin = checkin_repo.create_checkin(
        employee_id=employee.id,
        group_chat_id=int(group_chat_id),
        latitude=float(latitude),
        longitude=float(longitude),
        photo_path=photo_path
    )

    return jsonify({
        'success': True,
        'message': 'Check-in recorded successfully',
        'check_in_id': checkin.id
    }), 201
```

---

## Database Migration

**Create Alembic Migration:**

```bash
alembic revision -m "add_employee_groups_mapping_table"
```

**Migration File:**

```python
# alembic/versions/XXXX_add_employee_groups_mapping_table.py

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Create employee_groups table
    op.create_table(
        'employee_groups',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('employee_id', sa.Integer, nullable=False),
        sa.Column('group_chat_id', sa.BigInteger, nullable=False),
        sa.Column('joined_at', sa.TIMESTAMP, server_default=sa.func.current_timestamp()),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
    )

    # Add foreign key constraints
    op.create_foreign_key(
        'fk_employee_groups_employee',
        'employee_groups', 'employees',
        ['employee_id'], ['id'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'fk_employee_groups_group',
        'employee_groups', 'groups',
        ['group_chat_id'], ['chat_id'],
        ondelete='CASCADE'
    )

    # Add unique constraint
    op.create_unique_constraint(
        'uq_employee_group',
        'employee_groups',
        ['employee_id', 'group_chat_id']
    )

    # Add indexes
    op.create_index('idx_employee_groups_employee', 'employee_groups', ['employee_id'])
    op.create_index('idx_employee_groups_group', 'employee_groups', ['group_chat_id'])


def downgrade():
    op.drop_index('idx_employee_groups_group', 'employee_groups')
    op.drop_index('idx_employee_groups_employee', 'employee_groups')
    op.drop_constraint('fk_employee_groups_group', 'employee_groups', type_='foreignkey')
    op.drop_constraint('fk_employee_groups_employee', 'employee_groups', type_='foreignkey')
    op.drop_constraint('uq_employee_group', 'employee_groups', type_='unique')
    op.drop_table('employee_groups')
```

**Run Migration:**

```bash
alembic upgrade head
```

---

## Testing Guide

### Test Scenario 1: New Business Registration

**Steps:**
1. Create a Telegram group: "Test Company"
2. Add @OALocal_bot to the group
3. Add test employees to the group
4. Run `/register` command
5. Enter business name: "Test Company Inc."
6. Verify bot confirms registration

**Expected Result:**
✅ Group is registered in database
✅ Message says to use `/menu` command
✅ Instructions mention employees should be in group

---

### Test Scenario 2: Employee Using Menu Command

**Steps:**
1. As an employee (member of the group), open the Test Company group
2. Run `/menu` command
3. Verify bot shows inline keyboard with buttons
4. Click "✅ Check In" button
5. Verify miniapp opens

**Expected Result:**
✅ Menu shows buttons: Check In, View Balance, My Reports
✅ Each button is clickable
✅ Miniapp opens with group auto-selected
✅ No manual group selection needed

---

### Test Scenario 3: Employee First Check-In

**Steps:**
1. Run `/menu` in group
2. Click "Check In" button
3. Miniapp opens
4. Allow location and camera permissions
5. Take photo
6. Submit check-in

**Expected Result:**
✅ Group is auto-selected (business name shown)
✅ Check-in is saved with correct group_chat_id
✅ Employee-group association is created in database
✅ Success message is shown

**Database Verification:**
```sql
-- Check employee_groups table
SELECT * FROM employee_groups WHERE employee_id = [employee_id];

-- Should show one row with the group_chat_id
```

---

### Test Scenario 4: Incorrect Access (No Deep Link)

**Steps:**
1. Open miniapp directly from bot chat (not via /menu)
2. Observe error message

**Expected Result:**
✅ Shows "Incorrect Access" message
✅ Explains how to use /menu command
✅ Action buttons are disabled

---

## Summary

### What We Built

1. **Simple Registration Flow**
   - Admin runs `/register` in group
   - System generates and stores group-specific deep link
   - No need to share links manually

2. **Menu Command Access**
   - Employees run `/menu` in their business group
   - Bot shows inline keyboard with action buttons
   - Each button includes group context via deep link

3. **Automatic Group Context**
   - Deep link parameter: `startapp=group_ID`
   - Miniapp parses and auto-selects group
   - Zero manual selection needed

4. **User-Group Mapping Database**
   - `employee_groups` table tracks which employees belong to which groups
   - Auto-created on first check-in
   - Enables accurate reporting per business

### Benefits

✅ **Zero Friction for Employees**
- Run `/menu` → Click button → Automatic group selection
- No links to save or manage
- No manual configuration needed

✅ **Self-Service Access**
- Employees don't need to ask admin for links
- Always accessible via `/menu` command
- Can't lose access as long as they're in the group

✅ **Easy for Business Admins**
- One-time setup with `/register` command
- Just add employees to Telegram group
- No link distribution needed

✅ **Accurate Reporting**
- Every check-in is associated with the correct group
- Reports can be filtered by business
- No ambiguity or manual data entry

✅ **Simple Architecture**
- Only ONE way to access: via `/menu` command
- No complex multi-group selection logic
- Easy to explain and support

---

## Next Steps

1. **Implement the code** following the examples above
2. **Run database migration** to create `employee_groups` table
3. **Test with real Telegram groups** using the testing guide
4. **Add UI elements** in miniapp (HTML/CSS for group selector)
5. **Deploy and share** deep links with employees

---

## Additional Enhancements (Optional)

### 1. QR Code Generation

Generate QR codes for each group's deep link for easy sharing:

```python
import qrcode
from io import BytesIO

def generate_qr_code(deep_link: str) -> BytesIO:
    """Generate QR code for deep link"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(deep_link)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    return buf

# In registration handler
qr_image = generate_qr_code(deep_link)
await context.bot.send_photo(
    chat_id=chat.id,
    photo=qr_image,
    caption="Scan this QR code to open the miniapp!"
)
```

### 2. Group Invitation Codes

Short codes for manual entry:

```python
import secrets

def generate_invite_code(length=6):
    """Generate short alphanumeric invite code"""
    return secrets.token_urlsafe(length)[:length].upper()

# Store in database
group.invite_code = generate_invite_code()
```

Employees can enter code in miniapp to join group.

### 3. Group Permissions

Add role-based permissions:

```sql
ALTER TABLE employee_groups ADD COLUMN role VARCHAR(20) DEFAULT 'employee';
-- Roles: 'admin', 'manager', 'employee'
```

---

**Document Version:** 1.0
**Last Updated:** 2025-12-26
**Status:** Ready for Implementation