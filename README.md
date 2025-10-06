# Office Automation Bot

A Telegram bot for SME management built with Domain-Driven Design (DDD) architecture.

## Features

- **Group Management**: Automatically creates and manages Telegram groups for organizations
- **Check-In**: Employees can check in from group chats by sharing their location
- **Employee-Group Association**: Automatically adds employees to groups when they check in
- **Salary Advance**: Admins can record salary advance payments to employees

## Tech Stack

- Python 3.13
- python-telegram-bot 22.5
- SQLAlchemy 2.0.43
- MySQL 8
- Alembic (database migrations)

## Project Structure (DDD)

```
office-automation/
├── main.py                           # Entry point
├── alembic/                          # Database migrations
│   └── versions/
├── src/
│   ├── domain/                       # Core business logic
│   │   ├── entities/                 # Business entities
│   │   ├── value_objects/            # Immutable value objects
│   │   └── repositories/             # Repository interfaces
│   │
│   ├── application/                  # Use cases/business rules
│   │   ├── use_cases/
│   │   └── dto/                      # Data transfer objects
│   │
│   ├── infrastructure/               # External concerns
│   │   ├── config/
│   │   ├── persistence/              # Database implementations
│   │   └── telegram/
│   │
│   └── presentation/                 # User interface
│       └── handlers/
```

## Setup

### 1. Prerequisites

- Python 3.13+
- MySQL 8
- Telegram Bot Token (get from [@BotFather](https://t.me/botfather))

### 2. Database Setup

Create MySQL database:

```sql
CREATE DATABASE office_automation CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Update `.env` with your credentials:

```env
BOT_TOKEN=your_telegram_bot_token

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=office_automation
```

Update admin IDs in `main.py`:

```python
settings.load_admin_ids([
    123456789,  # Replace with your Telegram user ID
])
```

To get your Telegram ID, message [@userinfobot](https://t.me/userinfobot)

### 4. Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head
```

### 5. Run

```bash
python main.py
```

The bot will start and display "Bot is running..."

## Bot Commands

- `/start` - Register or show main menu
- `/cancel` - Cancel current operation
- `/checkin` - Open the check-in options in a private chat

## Usage

### Setup

1. **Create a Telegram group** for your organization
2. **Add the bot** to the group as an admin
3. **Add employees** to the group

### For Employees

1. **Register** (one-time):
   - Start a private chat with the bot
   - Send `/start`
   - Enter your full name

2. **Check In** (daily):
   - Go to your organization's group chat
   - Type any message (e.g., "check in")
   - Click "📍 Check In" when prompted
   - Share your location
   - The bot will automatically:
     - Register the group (if first time)
     - Add you to the group members
     - Record your check-in with location and timestamp

### For Admins

1. Start a private chat with the bot
2. Click "💰 Record Salary Advance"
3. Enter employee name
4. Enter amount
5. Enter optional note or type 'skip'

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## Development

The project follows Domain-Driven Design principles:

- **Domain Layer**: Contains core business logic, independent of frameworks
- **Application Layer**: Use cases that orchestrate domain objects
- **Infrastructure Layer**: Database, external services, framework code
- **Presentation Layer**: Telegram bot handlers

## Adding New Features

1. Define entity in `src/domain/entities/`
2. Create repository interface in `src/domain/repositories/`
3. Implement repository in `src/infrastructure/persistence/`
4. Create use case in `src/application/use_cases/`
5. Add handler in `src/presentation/handlers/`
6. Register handler in `src/infrastructure/telegram/bot_app.py`
7. Create migration with `alembic revision --autogenerate -m "feature_name"`
