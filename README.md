# Office Automation Bot

A Telegram bot for SME management built with Domain-Driven Design (DDD) architecture.

## Features

- **Check-In**: Employees can check in by sharing their location
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

## Usage

### For Employees

1. Start the bot with `/start`
2. Register by entering your name
3. Click "📍 Check In" to share your location

### For Admins

1. Click "💰 Record Salary Advance"
2. Enter employee name
3. Enter amount
4. Enter optional note

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
