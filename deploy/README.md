# Deployment Guide

This directory contains deployment configurations for the Office Automation system.

## Service Deployment

The system runs both bots (Check-in Bot and Balance Bot) in a single service using multiprocessing.

**Deploy:**
```bash
sudo cp deploy/office-automation.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start office-automation
sudo systemctl enable office-automation
```

## Service Management

### Check Status
```bash
sudo systemctl status office-automation
```

### View Logs
```bash
# Follow live logs
sudo journalctl -u office-automation -f

# View recent logs
sudo journalctl -u office-automation -n 100
```

### Restart Service
```bash
sudo systemctl restart office-automation
```

### Stop Service
```bash
sudo systemctl stop office-automation
```

## GitHub Secrets Required

Add these secrets to your GitHub repository:

### Bot Configuration
- `CHECKIN_BOT_TOKEN` - Token for check-in bot
- `BALANCE_BOT_TOKEN` - Token for balance bot

### Database Configuration
- `DB_HOST` - Database host
- `DB_PORT` - Database port (default: 3306)
- `DB_USER` - Database username
- `DB_PASSWORD` - Database password
- `DB_NAME` - Database name

### Google Sheets Configuration
- `GOOGLE_SHEETS_CREDENTIALS` - Full JSON content of credentials.json
- `GOOGLE_SHEETS_CREDENTIALS_FILE` - Path to credentials file (default: credentials.json)
- `BALANCE_SHEET_ID` - Google Sheets spreadsheet ID
- `BALANCE_SHEET_NAME` - Sheet name (optional, auto-generated from month)

### Deployment Configuration
- `SSH_HOST` - Server hostname/IP
- `SSH_USERNAME` - SSH username
- `SSH_PASSWORD` - SSH password
- `SSH_PORT` - SSH port (default: 22)
- `REMOTE_APP_DIR` - Application directory on server (e.g., /root/office-automation)

## GitHub Actions Workflow

The `deploy.yml` workflow automatically deploys both bots to your server when you push to the main branch. The deployment will:
- Pull the latest code
- Update dependencies
- Create/update `.env` and `credentials.json`
- Run database migrations
- Restart the service
