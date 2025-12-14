# OpnForm Integration Blueprint

## Executive Summary

This blueprint outlines the architecture and implementation plan for integrating OpnForm (open-source form builder) with our Telegram-based office automation system. The integration enables customers to fill out custom forms via Telegram miniapp, with automatic webhook processing and report generation.

**Key Goals:**
- Zero-code customer onboarding (no code changes per customer)
- Self-service form creation via OpnForm UI
- Flexible form submission handling via webhooks
- Daily/monthly reporting via Telegram bot and miniapp

---

## 1. System Architecture Overview

### Current System (MySQL-based)
```
┌─────────────────────────────────────────────────────────┐
│                    Current System                       │
├─────────────────────────────────────────────────────────┤
│  - Tech Stack: Python + Flask + python-telegram-bot     │
│  - Database: MySQL (SQLAlchemy ORM)                     │
│  - Architecture: Domain-Driven Design (DDD)             │
│  - 3 Processes: CheckIn Bot, Balance Bot, Flask API     │
│  - Auth: Telegram Web App (HMAC-SHA256)                 │
└─────────────────────────────────────────────────────────┘
```

### New OpnForm Integration (MongoDB-based)
```
┌─────────────────────────────────────────────────────────┐
│                 OpnForm Integration                     │
├─────────────────────────────────────────────────────────┤
│  - Database: MongoDB (form submissions in JSON)         │
│  - Integration: OpnForm webhooks with HMAC signature    │
│  - Features: Multi-tenant, per-customer webhooks        │
│  - Reporting: Aggregation pipeline for daily/monthly    │
│  - Admin Portal: Vue 3 SPA for customer/form management │
└─────────────────────────────────────────────────────────┘
```

---

## 2. OpnForm Capabilities

Based on research from [OpnForm Technical Docs](https://docs.opnform.com/api-reference/integrations/webhook-security) and [OpnForm Help](https://help.opnform.com/en/article/can-i-trigger-another-service-whenever-my-form-requires-a-submission-webhooks-6nrnfn/):

### Webhook Features
- **Webhook URL Configuration**: Per-form webhook endpoint setup
- **Security**: HMAC-SHA256 signature validation with webhook secret
- **Custom Headers**: Support for API keys, authorization tokens
- **Conditional Webhooks**: Trigger webhooks based on field conditions
- **Availability**: Pro and Team subscriptions only

### API Features
- **REST API**: Base URL `https://api.opnform.com`
- **Authentication**: JWT Bearer tokens
- **Resources**: Workspaces, forms, submissions management
- **Dashboard**: Token creation and management

### Integration Pattern
```
User Submits Form → OpnForm → Webhook POST → Our Server → MongoDB
```

---

## 3. Data Architecture

### 3.1 Dual Database Strategy

**MySQL (Existing)**: Core business data
- Employees, groups, check-ins
- Salary advances, allowances
- Vehicle operations
- Package subscriptions

**MongoDB (New)**: Form submission data
- Raw webhook payloads (JSON)
- Customer form configurations
- Form submission history
- Aggregated reports cache

### 3.2 MongoDB Schema Design

#### Collection: `customers`
```javascript
{
  _id: ObjectId,
  telegram_user_id: String,           // Telegram user ID (indexed)
  business_name: String,              // Business/company name
  telegram_group_id: String,          // Telegram group chat ID (indexed)
  package_level: String,              // "free", "basic", "premium"
  webhook_secret: String,             // For validating OpnForm webhooks
  webhook_endpoint: String,           // Generated endpoint: /webhook/<customer_id>
  status: String,                     // "active", "inactive", "suspended"
  created_at: ISODate,
  updated_at: ISODate
}

// Indexes
customers.createIndex({ telegram_user_id: 1 }, { unique: true })
customers.createIndex({ telegram_group_id: 1 })
customers.createIndex({ webhook_endpoint: 1 }, { unique: true })
```

#### Collection: `form_configurations`
```javascript
{
  _id: ObjectId,
  customer_id: ObjectId,              // Reference to customers collection
  opnform_form_id: String,            // OpnForm's form ID (indexed)
  opnform_workspace_id: String,       // OpnForm workspace ID
  form_name: String,                  // Descriptive name
  form_slug: String,                  // URL-friendly identifier
  webhook_url: String,                // Full webhook URL configured in OpnForm
  webhook_secret: String,             // Secret for this specific form
  field_mapping: Object,              // Map OpnForm fields to our field names
  is_active: Boolean,
  created_at: ISODate,
  updated_at: ISODate
}

// Indexes
form_configurations.createIndex({ customer_id: 1, opnform_form_id: 1 }, { unique: true })
form_configurations.createIndex({ customer_id: 1, is_active: 1 })
```

#### Collection: `form_submissions`
```javascript
{
  _id: ObjectId,
  customer_id: ObjectId,              // Reference to customers collection
  form_config_id: ObjectId,           // Reference to form_configurations
  opnform_form_id: String,            // OpnForm's form ID (indexed)
  opnform_submission_id: String,      // OpnForm's submission ID (indexed)
  submission_data: Object,            // Raw form data from OpnForm (flexible schema)
  normalized_data: Object,            // Transformed data based on field_mapping
  metadata: {
    ip_address: String,
    user_agent: String,
    submitted_at: ISODate,            // When user submitted in OpnForm
    received_at: ISODate              // When our webhook received it
  },
  webhook_verified: Boolean,          // HMAC signature validation result
  processing_status: String,          // "pending", "processed", "failed"
  processing_errors: Array,           // Error messages if processing failed
  created_at: ISODate
}

// Indexes
form_submissions.createIndex({ customer_id: 1, created_at: -1 })
form_submissions.createIndex({ form_config_id: 1, created_at: -1 })
form_submissions.createIndex({ opnform_submission_id: 1 }, { unique: true })
form_submissions.createIndex({ "metadata.submitted_at": -1 })
form_submissions.createIndex({ processing_status: 1 })

// TTL index for data retention (optional)
form_submissions.createIndex({ created_at: 1 }, { expireAfterSeconds: 31536000 }) // 1 year
```

#### Collection: `report_cache`
```javascript
{
  _id: ObjectId,
  customer_id: ObjectId,
  form_config_id: ObjectId,
  report_type: String,                // "daily", "monthly", "custom"
  report_date: ISODate,               // Date for daily, month start for monthly
  aggregated_data: Object,            // Pre-computed statistics
  submission_count: Number,
  generated_at: ISODate,
  expires_at: ISODate
}

// Indexes
report_cache.createIndex({ customer_id: 1, form_config_id: 1, report_type: 1, report_date: -1 })
report_cache.createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 }) // TTL index
```

---

## 4. Admin Portal (Vue 3 SPA)

### 4.1 Overview

A modern Single Page Application (SPA) will be built using Vue 3 to provide administrators with a web-based interface for managing OpnForm integrations. This is separate from the customer-facing Telegram bot interface.

**Purpose:**
- Centralized admin dashboard for managing customers and forms
- Visual interface for viewing webhook logs and analytics
- Real-time monitoring of form submissions
- Customer onboarding workflow
- System health monitoring

**Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│              Admin Portal (Vue 3 SPA)                   │
├─────────────────────────────────────────────────────────┤
│  Frontend:      Vue 3 + Vite                            │
│  UI Framework:  Element Plus / Ant Design Vue           │
│  State:         Pinia                                   │
│  Auth:          Telegram Login Widget + JWT            │
│  Deployment:    Static hosting (Nginx/Vercel/S3)       │
└────────────────────┬────────────────────────────────────┘
                     │ REST API (Axios)
┌────────────────────▼────────────────────────────────────┐
│            Flask Backend API                            │
│  - /api/opnform/customers (CRUD)                       │
│  - /api/opnform/forms (CRUD)                           │
│  - /api/opnform/submissions (Analytics)                │
│  - /api/opnform/webhooks/logs                          │
│  - /api/auth/telegram-login                            │
└─────────────────────────────────────────────────────────┘
```

### 4.2 Key Features

#### Dashboard View
- **Metrics Cards**: Total customers, active forms, submissions (today/month)
- **Recent Activity**: Latest webhook events with status indicators
- **Quick Stats**: Success/failure rates, avg processing time
- **Quick Actions**: Register customer, link form, view logs

#### Customers Management
- **Customer List**: Searchable/filterable table with pagination
- **Customer Details**: View webhook URL, secret, linked forms
- **Actions**: Create, edit, activate/deactivate, copy webhook URL
- **Bulk Operations**: Export customer list, bulk status updates

#### Forms Management
- **Form Configuration**: Link OpnForm forms to customers
- **Field Mapping**: Visual editor for field name mapping
- **Form Testing**: Send test webhooks to verify configuration
- **Form Stats**: Submission counts, last submission time

#### Webhook Logs Viewer
- **Real-time Log Stream**: Live webhook events as they arrive
- **Filtering**: By customer, form, date range, status
- **Log Details**: Full payload inspection, validation results
- **Error Tracking**: Failed webhooks with retry options

#### Analytics Dashboard
- **Submission Charts**: Daily/monthly trends (Chart.js/ECharts)
- **Customer Rankings**: Top customers by submission volume
- **Form Usage**: Most popular forms, completion rates
- **Export Tools**: Download reports as CSV/JSON

### 4.3 Technology Stack

**Frontend:**
```json
{
  "framework": "Vue 3.4+",
  "build_tool": "Vite 5+",
  "ui_library": "Element Plus or Ant Design Vue",
  "state_management": "Pinia",
  "routing": "Vue Router 4",
  "http_client": "Axios",
  "charts": "Chart.js or Apache ECharts",
  "language": "TypeScript (recommended)"
}
```

**Authentication:**
- Telegram Login Widget for admin authentication
- JWT tokens for API authorization
- Admin whitelist stored in environment variables or database
- Token refresh mechanism

**API Integration:**
- RESTful API communication with Flask backend
- Axios interceptors for auth token injection
- Error handling and retry logic
- Request/response logging

### 4.4 Admin Portal Routes

```
/login              - Telegram login widget
/dashboard          - Overview metrics and quick actions
/customers          - Customer list and management
/customers/:id      - Customer details and forms
/customers/:id/forms/new - Link new form wizard
/forms              - All forms across customers
/webhooks/logs      - Webhook activity log viewer
/analytics          - Charts and reports
/settings           - System configuration
```

### 4.5 Deployment Strategy

**Development:**
- Frontend dev server: `http://localhost:5173` (Vite)
- Backend API: `http://localhost:5000` (Flask)
- Vite proxy configuration for API requests

**Production:**
- Build static assets: `npm run build` → `dist/` folder
- Serve via Nginx or CDN (Vercel, Netlify, S3+CloudFront)
- API reverse proxy through Nginx
- HTTPS required for Telegram Login Widget

**Docker Integration:**
```yaml
# New service in compose.yaml
admin-portal:
  image: nginx:alpine
  volumes:
    - ./admin-portal/dist:/usr/share/nginx/html
    - ./nginx.conf:/etc/nginx/nginx.conf
  ports:
    - "3000:80"
  depends_on:
    - flask_api
```

---

## 5. Customer Onboarding Flow

### 5.1 Onboarding via Admin Portal (Primary Method)

**Step 1: Admin logs into Admin Portal**
- Navigate to `https://admin.yourdomain.com`
- Click "Login with Telegram"
- Authorize with Telegram (admin whitelist check)
- Redirected to dashboard

**Step 2: Register new customer**
- Click "Register New Customer" button
- Fill form:
  - Business name
  - Telegram user ID (admin can get from bot)
  - Telegram group ID
  - Package level (dropdown: free/basic/premium)
- Submit form
- System generates:
  - Unique customer_id
  - Webhook URL: `https://yourdomain.com/webhook/{customer_id}`
  - Webhook secret (32-byte random)
- Display success modal with:
  - ✅ Customer created
  - 📋 Webhook URL (copy button)
  - 🔑 Webhook secret (copy button, show/hide toggle)
  - 📝 Next steps instructions

**Step 3: Admin creates form in OpnForm**
- Admin goes to OpnForm.com (separate tab)
- Creates form using drag-and-drop builder
- Notes the form ID from OpnForm UI
- Configures webhook in OpnForm:
  - URL: (paste from admin portal)
  - Secret: (paste from admin portal)
  - Test webhook → success

**Step 4: Link form in Admin Portal**
- Return to admin portal
- Navigate to customer details page
- Click "Link New Form"
- Fill wizard:
  - OpnForm form ID
  - Form name (descriptive)
  - Field mapping (optional JSON or key-value UI)
- Submit
- System validates and saves configuration
- Display success notification

**Step 5: Verify setup**
- Admin portal shows "Send Test Submission" button
- Click to trigger test webhook from OpnForm
- View real-time log in webhook viewer
- ✅ Setup complete!

### 5.2 Alternative: Onboarding via Telegram Bot

For admins who prefer command-line style interaction, Telegram bot commands are still available:

### 5.3 Sequence Diagram (Admin Portal Flow)

```
Admin                    Admin Portal (Vue)       Flask API               OpnForm              MongoDB
     |                              |                        |                      |                    |
     |--1. Login with Telegram----->|                        |                      |                    |
     |                              |                        |                      |                    |
     |                              |--2. POST /api/auth/telegram-login             |                    |
     |                              |                        |                      |                    |
     |<-3. JWT token + redirect-----|                        |                      |                    |
     |                              |                        |                      |                    |
     |--4. Click "Register Customer"|                        |                      |                    |
     |--5. Fill form (business info)|                        |                      |                    |
     |                              |                        |                      |                    |
     |                              |--6. POST /api/opnform/customers               |                    |
     |                              |                        |                      |                    |
     |                              |                        |--5. Generate webhook endpoint             |
     |                              |                        |    Generate secret                        |
     |                              |                        |                      |                    |
     |                              |                        |--6. Save customer--->|------------------->|
     |                              |                        |                      |                    |
     |                              |                        |<-7. Return webhook URL, secret------------|
     |                              |                        |                      |                    |
     |                              |<-8. Customer created---|                      |                    |
     |                              |                        |                      |                    |
     |<-9. Webhook URL & Instructions                        |                      |                    |
     |    (Copy URL, go to OpnForm) |                        |                      |                    |
     |                              |                        |                      |                    |
     |--10. Go to OpnForm UI--------|--------------------->(Opens Browser)--------->|                    |
     |                              |                        |                      |                    |
     |--13. Create form in OpnForm-------------------------->|                      |                    |
     |--14. Note form ID            |                        |                      |                    |
     |                              |                        |                      |                    |
     |--15. Configure webhook (OpnForm)--------------------->|                      |                    |
     |     Paste webhook URL & secret                        |                      |                    |
     |     Add custom headers (optional)                     |                      |                    |
     |                              |                        |                      |                    |
     |--16. Test webhook (OpnForm)-------------------------->|                      |                    |
     |                              |                        |                      |                    |
     |                              |                        |<--14. POST /webhook/<customer_id>---------|
     |                              |                        |      (Test submission)                    |
     |                              |                        |                      |                    |
     |                              |                        |--15. Validate HMAC   |                    |
     |                              |                        |                      |                    |
     |                              |                        |--16. Save test submission---------------->|
     |                              |                        |                      |                    |
     |                              |                        |--17. Return 200 OK-->|                    |
     |                              |                        |                      |                    |
     |<-18. Test successful!--------|---------------------<(OpnForm shows success)  |                    |
     |                              |                        |                      |                    |
     |--19. /link_form------------->|                        |                      |                    |
     |     Provide OpnForm form ID  |                        |                      |                    |
     |                              |                        |                      |                    |
     |                              |--20. POST /api/opnform/forms                  |                    |
     |                              |                        |                      |                    |
     |                              |                        |--21. Save form config-------------------->|
     |                              |                        |                      |                    |
     |<-22. Setup complete!---------|                        |                      |                    |
     |     Form is now active       |                        |                      |                    |
```

### 5.4 Implementation Steps

#### Method A: Admin Portal (Recommended)

See section 5.1 above for the complete Admin Portal onboarding flow.

#### Method B: Telegram Bot Command (Alternative)

**Command**: `/register_opnform`

**Conversation Flow**:
1. Bot asks: "What is your business name?"
2. User provides: "ABC Company"
3. Bot asks: "What is your Telegram group ID?" (or auto-detect if in group)
4. User provides or confirms
5. Bot calls API to create customer

**API Endpoint**: `POST /api/opnform/customers`
```json
{
  "telegram_user_id": "123456789",
  "business_name": "ABC Company",
  "telegram_group_id": "-1001234567890",
  "package_level": "basic"
}
```

**Backend Processing**:
```python
1. Generate unique customer_id (MongoDB ObjectId)
2. Generate webhook_secret (secure random string, 32 bytes)
3. Generate webhook_endpoint: f"/webhook/{customer_id}"
4. Create customer record in MongoDB
5. Return webhook URL and secret to user
```

**Response**:
```json
{
  "customer_id": "507f1f77bcf86cd799439011",
  "webhook_url": "https://yourdomain.com/webhook/507f1f77bcf86cd799439011",
  "webhook_secret": "wh_sec_abc123...",
  "next_steps": "Go to OpnForm.com, create a form, and configure this webhook URL"
}
```

#### Step 2: Create Webhook Endpoint
**No action needed** - Endpoint is dynamically generated and ready to receive webhooks

**Endpoint**: `POST /webhook/<customer_id>`

**Expected Webhook Payload** (from OpnForm):
```json
{
  "form_id": "opnform_form_123",
  "submission_id": "sub_456",
  "workspace_id": "ws_789",
  "data": {
    "field_1": "value_1",
    "field_2": "value_2",
    "field_3": "value_3"
  },
  "submitted_at": "2025-12-11T10:30:00Z"
}
```

**Headers** (from OpnForm):
```
X-OpnForm-Signature: sha256=abc123...
Content-Type: application/json
```

#### Step 3: Create Form in OpnForm (Manual)
**User Actions**:
1. Go to https://opnform.com
2. Login/signup
3. Create new form using drag-and-drop builder
4. Add fields (text, number, date, dropdown, file upload, etc.)
5. Customize form design and validation rules
6. Note the Form ID from URL or settings

#### Step 4: Configure Webhook in OpnForm (Manual)
**User Actions**:
1. In form settings, go to "Integrations" tab
2. Select "Webhook Notification"
3. Toggle to enable
4. Paste webhook URL: `https://yourdomain.com/webhook/507f1f77bcf86cd799439011`
5. Enter webhook secret: `wh_sec_abc123...`
6. (Optional) Add custom headers for additional security
7. Click "Save"
8. Click "Test Webhook" to verify

#### Step 5: Link Form Configuration (Telegram Bot Command)
**Command**: `/link_form`

**Conversation Flow**:
1. Bot asks: "What is your OpnForm form ID?"
2. User provides: "opnform_form_123"
3. Bot asks: "What should we call this form?"
4. User provides: "Daily Operation Notes"
5. Bot asks: "Do you want to map fields? (optional)"
6. User can provide field mapping or skip

**API Endpoint**: `POST /api/opnform/forms`
```json
{
  "customer_id": "507f1f77bcf86cd799439011",
  "opnform_form_id": "opnform_form_123",
  "form_name": "Daily Operation Notes",
  "form_slug": "daily-operation-notes",
  "field_mapping": {
    "field_1": "date",
    "field_2": "operation_type",
    "field_3": "notes"
  }
}
```

**Backend Processing**:
```python
1. Validate customer_id exists
2. Generate webhook_secret for this form (or reuse customer secret)
3. Create form_configuration record
4. Set is_active = True
5. Return success
```

---

## 6. Daily Operations Flow

### 6.1 Form Submission Flow

```
User in Telegram    Telegram MiniApp    OpnForm    Flask Webhook    MongoDB    Telegram Bot
     |                     |                |             |             |             |
     |--1. Click "Fill Form" from bot menu->|             |             |             |
     |                     |                |             |             |             |
     |<-2. Open MiniApp with form link------|             |             |             |
     |                     |                |             |             |             |
     |--3. Open form------>|                |             |             |             |
     |                     |                |             |             |             |
     |                     |--4. Load form->|             |             |             |
     |                     |                |             |             |             |
     |                     |<-5. Form HTML--|             |             |             |
     |                     |                |             |             |             |
     |--6. Fill form------>|                |             |             |             |
     |                     |                |             |             |             |
     |--7. Submit--------->|                |             |             |             |
     |                     |                |             |             |             |
     |                     |--8. POST------>|             |             |             |
     |                     |                |             |             |             |
     |                     |                |-9. Webhook->|             |             |
     |                     |                |             |             |             |
     |                     |                |             |--10. Validate HMAC        |
     |                     |                |             |             |             |
     |                     |                |             |--11. Save-->|             |
     |                     |                |             |             |             |
     |                     |                |             |--12. 200 OK->            |
     |                     |                |             |             |             |
     |                     |                |<-13. Success|             |             |
     |                     |                |             |             |             |
     |<-14. Success message|                |             |             |             |
     |                     |                |             |             |             |
     |                     |                |             |--15. Async process------->|
     |                     |                |             |             |             |
     |<-16. Notification (optional)---------|-------------|-------------|------------>|
     |     "New submission received"        |             |             |             |
```

### 6.2 Multiple Submissions Per Day
- **Supported**: Users can submit the same form multiple times
- **Storage**: Each submission is a separate document in `form_submissions`
- **Tracking**: Indexed by `customer_id` and `created_at` for efficient queries

---

## 7. Reporting System

### 7.1 Report Types

Reports are accessible via:
1. **Telegram Bot**: `/daily_report`, `/monthly_report` commands
2. **Admin Portal**: Analytics dashboard with interactive charts

#### Daily Report
**Trigger**: Bot command `/daily_report` or MiniApp button

**Query**:
```javascript
// Aggregate submissions for today
db.form_submissions.aggregate([
  {
    $match: {
      customer_id: ObjectId("507f1f77bcf86cd799439011"),
      "metadata.submitted_at": {
        $gte: ISODate("2025-12-11T00:00:00Z"),
        $lt: ISODate("2025-12-12T00:00:00Z")
      },
      processing_status: "processed"
    }
  },
  {
    $group: {
      _id: "$form_config_id",
      count: { $sum: 1 },
      submissions: { $push: "$normalized_data" }
    }
  },
  {
    $lookup: {
      from: "form_configurations",
      localField: "_id",
      foreignField: "_id",
      as: "form_info"
    }
  }
])
```

**Report Format** (Telegram message):
```
📊 Daily Report - December 11, 2025

📝 Daily Operation Notes
   Submissions: 5
   - Operation Type: Delivery (3)
   - Operation Type: Pickup (2)

📝 Expense Report
   Submissions: 2
   Total Amount: $250.00

📝 Attendance Check
   Submissions: 12
   Present: 10, Absent: 2
```

#### Monthly Report
**Trigger**: Bot command `/monthly_report <month>` or MiniApp button

**Query**:
```javascript
// Aggregate submissions for the month
db.form_submissions.aggregate([
  {
    $match: {
      customer_id: ObjectId("507f1f77bcf86cd799439011"),
      "metadata.submitted_at": {
        $gte: ISODate("2025-12-01T00:00:00Z"),
        $lt: ISODate("2026-01-01T00:00:00Z")
      },
      processing_status: "processed"
    }
  },
  {
    $group: {
      _id: {
        form_id: "$form_config_id",
        day: { $dayOfMonth: "$metadata.submitted_at" }
      },
      count: { $sum: 1 }
    }
  },
  {
    $group: {
      _id: "$_id.form_id",
      total_count: { $sum: "$count" },
      daily_breakdown: {
        $push: {
          day: "$_id.day",
          count: "$count"
        }
      }
    }
  }
])
```

**Report Format** (Telegram message with chart):
```
📊 Monthly Report - December 2025

📝 Daily Operation Notes
   Total Submissions: 150
   Average per day: 5
   Most active day: Dec 15 (12 submissions)

   📈 Trend Chart:
   Week 1: ▁▂▃▄▅▆▇
   Week 2: ▅▆▇▇▆▅▄
   Week 3: ▄▅▆▇▇▆▅
   Week 4: ▆▇▇▆▅▄▃
```

### 7.2 Report Caching Strategy

**Purpose**: Reduce database queries for frequently accessed reports

**Implementation**:
```python
# Pseudo-code
def get_daily_report(customer_id, date):
    # Check cache first
    cache_key = f"{customer_id}:{date}:daily"
    cached = report_cache.find_one({
        "customer_id": customer_id,
        "report_date": date,
        "report_type": "daily"
    })

    if cached and not is_expired(cached):
        return cached["aggregated_data"]

    # Generate new report
    report = generate_daily_report(customer_id, date)

    # Cache for 1 hour (for today) or 24 hours (for past days)
    ttl = 3600 if is_today(date) else 86400

    report_cache.insert_one({
        "customer_id": customer_id,
        "report_date": date,
        "report_type": "daily",
        "aggregated_data": report,
        "generated_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(seconds=ttl)
    })

    return report
```

---

## 8. Technical Implementation Details

### 8.1 Technology Stack Additions

**Backend Dependencies**:
```python
# requirements.txt additions
pymongo==4.6.1                 # MongoDB driver
motor==3.3.2                   # Async MongoDB driver (optional, for async endpoints)
pydantic==2.5.3                # Data validation for MongoDB documents
python-dotenv==1.0.0           # Already exists, for MongoDB connection string
flask-jwt-extended==4.6.0      # JWT authentication for admin portal
flask-cors==4.0.0              # CORS support for SPA
```

**Admin Portal (Frontend) Dependencies**:
```json
{
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.0",
    "pinia": "^2.1.0",
    "axios": "^1.6.0",
    "element-plus": "^2.5.0",
    "chart.js": "^4.4.0",
    "vue-chartjs": "^5.3.0",
    "@vueuse/core": "^10.7.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "vite": "^5.0.0",
    "typescript": "^5.3.0",
    "sass": "^1.69.0"
  }
}
```

**Configuration** (`src/infrastructure/config/settings.py`):
```python
# MongoDB settings
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "office_automation_forms")
MONGODB_MAX_POOL_SIZE = int(os.getenv("MONGODB_MAX_POOL_SIZE", "10"))

# OpnForm settings
OPNFORM_WEBHOOK_BASE_URL = os.getenv("OPNFORM_WEBHOOK_BASE_URL", "https://yourdomain.com")
OPNFORM_API_BASE_URL = os.getenv("OPNFORM_API_BASE_URL", "https://api.opnform.com")
OPNFORM_API_TOKEN = os.getenv("OPNFORM_API_TOKEN", "")  # Optional: for API calls to OpnForm
```

### 8.2 Folder Structure (New Additions)

```
office-automation/
├── admin-portal/                       # NEW: Vue 3 Admin SPA
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   │   ├── styles/
│   │   │   └── images/
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Header.vue
│   │   │   │   ├── Sidebar.vue
│   │   │   │   └── Footer.vue
│   │   │   ├── customers/
│   │   │   │   ├── CustomerList.vue
│   │   │   │   ├── CustomerForm.vue
│   │   │   │   └── CustomerDetails.vue
│   │   │   ├── forms/
│   │   │   │   ├── FormConfigCard.vue
│   │   │   │   ├── FormLinkWizard.vue
│   │   │   │   └── FieldMapper.vue
│   │   │   ├── webhooks/
│   │   │   │   ├── WebhookLogViewer.vue
│   │   │   │   └── WebhookLogItem.vue
│   │   │   ├── analytics/
│   │   │   │   ├── SubmissionChart.vue
│   │   │   │   ├── CustomerRankings.vue
│   │   │   │   └── FormUsageStats.vue
│   │   │   └── common/
│   │   │       ├── MetricsCard.vue
│   │   │       └── DataTable.vue
│   │   ├── views/
│   │   │   ├── Login.vue
│   │   │   ├── Dashboard.vue
│   │   │   ├── Customers.vue
│   │   │   ├── CustomerDetail.vue
│   │   │   ├── Forms.vue
│   │   │   ├── WebhookLogs.vue
│   │   │   ├── Analytics.vue
│   │   │   └── Settings.vue
│   │   ├── router/
│   │   │   └── index.ts
│   │   ├── stores/
│   │   │   ├── auth.ts
│   │   │   ├── customers.ts
│   │   │   ├── forms.ts
│   │   │   └── webhooks.ts
│   │   ├── services/
│   │   │   ├── api.ts              # Axios instance
│   │   │   ├── customers.api.ts
│   │   │   ├── forms.api.ts
│   │   │   └── auth.api.ts
│   │   ├── types/
│   │   │   ├── customer.ts
│   │   │   ├── form.ts
│   │   │   └── webhook.ts
│   │   ├── utils/
│   │   │   ├── telegram-auth.ts
│   │   │   └── formatters.ts
│   │   ├── App.vue
│   │   └── main.ts
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── .env.development
│
├── src/
├── domain/
│   ├── entities/
│   │   ├── opnform_customer.py           # NEW: Customer entity
│   │   ├── form_configuration.py         # NEW: Form config entity
│   │   └── form_submission.py            # NEW: Submission entity
│   │
│   └── repositories/
│       ├── i_opnform_customer_repository.py    # NEW: Interface
│       ├── i_form_configuration_repository.py  # NEW: Interface
│       └── i_form_submission_repository.py     # NEW: Interface
│
├── application/
│   ├── use_cases/
│   │   ├── register_opnform_customer_use_case.py     # NEW
│   │   ├── link_form_configuration_use_case.py       # NEW
│   │   ├── process_webhook_submission_use_case.py    # NEW
│   │   ├── get_daily_report_use_case.py              # NEW
│   │   └── get_monthly_report_use_case.py            # NEW
│   │
│   └── dto/
│       ├── opnform_customer_dto.py       # NEW: Request/response DTOs
│       ├── form_configuration_dto.py     # NEW
│       └── form_submission_dto.py        # NEW
│
├── infrastructure/
│   ├── persistence/
│   │   ├── mongodb/                      # NEW: MongoDB implementations
│   │   │   ├── __init__.py
│   │   │   ├── connection.py             # MongoDB connection manager
│   │   │   ├── models.py                 # Pydantic models for documents
│   │   │   ├── opnform_customer_repository_impl.py
│   │   │   ├── form_configuration_repository_impl.py
│   │   │   └── form_submission_repository_impl.py
│   │   │
│   │   └── mysql/                        # Rename current 'persistence' folder
│   │       └── ... (existing MySQL repos)
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── opnform_routes.py         # NEW: Customer/form management API
│   │   │   ├── opnform_admin_routes.py   # NEW: Admin portal API endpoints
│   │   │   ├── webhook_routes.py         # NEW: Webhook receiver endpoints
│   │   │   └── auth_routes.py            # NEW: Authentication for admin portal
│   │   │
│   │   └── middleware/
│   │       ├── opnform_webhook_validator.py  # NEW: HMAC signature validation
│   │       ├── jwt_auth.py               # NEW: JWT authentication
│   │       └── cors.py                   # NEW: CORS configuration
│   │
│   └── telegram/
│       └── opnform_bot_handlers.py       # NEW: Bot commands for OpnForm
│
└── presentation/
    └── handlers/
        ├── opnform_customer_handler.py   # NEW: /register_opnform command
        ├── opnform_form_handler.py       # NEW: /link_form command
        └── opnform_report_handler.py     # NEW: /daily_report, /monthly_report commands
```

### 8.3 Admin Portal API Endpoints

The following REST API endpoints will be created to support the admin portal:

**Authentication:**
```
POST   /api/auth/telegram-login        # Verify Telegram auth, issue JWT
POST   /api/auth/refresh-token         # Refresh JWT token
POST   /api/auth/logout                # Invalidate token
GET    /api/auth/me                    # Get current admin user info
```

**Customer Management:**
```
GET    /api/opnform/customers          # List all customers (paginated)
POST   /api/opnform/customers          # Create new customer
GET    /api/opnform/customers/:id      # Get customer details
PUT    /api/opnform/customers/:id      # Update customer
DELETE /api/opnform/customers/:id      # Delete/deactivate customer
PATCH  /api/opnform/customers/:id/status  # Activate/deactivate
```

**Form Management:**
```
GET    /api/opnform/forms              # List all forms (all customers)
POST   /api/opnform/forms              # Link new form to customer
GET    /api/opnform/forms/:id          # Get form configuration
PUT    /api/opnform/forms/:id          # Update form configuration
DELETE /api/opnform/forms/:id          # Unlink form
GET    /api/opnform/customers/:id/forms  # Get customer's forms
```

**Webhook & Submissions:**
```
GET    /api/opnform/webhooks/logs      # Get webhook logs (filterable)
GET    /api/opnform/submissions        # Get submissions (filterable)
GET    /api/opnform/submissions/:id    # Get submission details
POST   /api/opnform/webhooks/test      # Send test webhook
```

**Analytics:**
```
GET    /api/opnform/analytics/dashboard    # Dashboard metrics
GET    /api/opnform/analytics/submissions  # Submission trends
GET    /api/opnform/analytics/customers    # Customer rankings
GET    /api/opnform/analytics/forms        # Form usage stats
```

**System:**
```
GET    /api/opnform/health             # System health check
GET    /api/opnform/stats              # Overall system stats
```

### 8.4 Core Components

#### Component 1: Admin Portal Authentication (JWT + Telegram)
**File**: `src/infrastructure/api/routes/auth_routes.py`

```python
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
import hmac
import hashlib
from datetime import timedelta

auth_bp = Blueprint("auth", __name__)

# Admin whitelist (can be moved to database)
ADMIN_TELEGRAM_IDS = os.getenv("ADMIN_TELEGRAM_IDS", "").split(",")

def verify_telegram_auth(auth_data: dict, bot_token: str) -> bool:
    """
    Verify Telegram Login Widget authentication data
    https://core.telegram.org/widgets/login#checking-authorization
    """
    check_hash = auth_data.pop('hash', None)
    if not check_hash:
        return False

    # Create data-check-string
    data_check_arr = [f"{k}={v}" for k, v in sorted(auth_data.items())]
    data_check_string = '\n'.join(data_check_arr)

    # Compute secret key (SHA256 of bot token)
    secret_key = hashlib.sha256(bot_token.encode()).digest()

    # Compute HMAC-SHA256
    computed_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(computed_hash, check_hash)

@auth_bp.route('/api/auth/telegram-login', methods=['POST'])
def telegram_login():
    """
    Authenticate admin user via Telegram Login Widget

    Expected payload:
    {
        "id": 123456789,
        "first_name": "John",
        "last_name": "Doe",
        "username": "johndoe",
        "photo_url": "https://...",
        "auth_date": 1234567890,
        "hash": "abc123..."
    }
    """
    data = request.json

    # Verify Telegram authentication
    bot_token = os.getenv("CHECKIN_BOT_TOKEN")
    if not verify_telegram_auth(data.copy(), bot_token):
        return jsonify({"error": "Invalid Telegram authentication"}), 401

    # Check if user is admin
    user_id = str(data['id'])
    if user_id not in ADMIN_TELEGRAM_IDS:
        logger.warning(f"Unauthorized login attempt from Telegram ID: {user_id}")
        return jsonify({"error": "Unauthorized. Admin access only."}), 403

    # Create JWT tokens
    access_token = create_access_token(
        identity=user_id,
        additional_claims={
            "first_name": data.get('first_name'),
            "username": data.get('username')
        },
        expires_delta=timedelta(hours=8)
    )

    refresh_token = create_refresh_token(
        identity=user_id,
        expires_delta=timedelta(days=30)
    )

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user_id,
            "first_name": data.get('first_name'),
            "last_name": data.get('last_name'),
            "username": data.get('username'),
            "photo_url": data.get('photo_url')
        }
    }), 200

@auth_bp.route('/api/auth/refresh-token', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token"""
    identity = get_jwt_identity()
    new_access_token = create_access_token(identity=identity)
    return jsonify({"access_token": new_access_token}), 200

@auth_bp.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated admin user"""
    user_id = get_jwt_identity()
    # Fetch user details from database or JWT claims
    return jsonify({
        "id": user_id,
        "role": "admin"
    }), 200
```

#### Component 2: MongoDB Connection Manager
**File**: `src/infrastructure/persistence/mongodb/connection.py`

```python
from pymongo import MongoClient
from pymongo.database import Database
from src.infrastructure.config.settings import (
    MONGODB_URL,
    MONGODB_DATABASE,
    MONGODB_MAX_POOL_SIZE
)

class MongoDBConnection:
    _instance = None
    _client = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self) -> Database:
        if self._client is None:
            self._client = MongoClient(
                MONGODB_URL,
                maxPoolSize=MONGODB_MAX_POOL_SIZE
            )
            self._db = self._client[MONGODB_DATABASE]
            self._create_indexes()
        return self._db

    def _create_indexes(self):
        # Customer indexes
        self._db.customers.create_index("telegram_user_id", unique=True)
        self._db.customers.create_index("telegram_group_id")
        self._db.customers.create_index("webhook_endpoint", unique=True)

        # Form configuration indexes
        self._db.form_configurations.create_index(
            [("customer_id", 1), ("opnform_form_id", 1)],
            unique=True
        )
        self._db.form_configurations.create_index([("customer_id", 1), ("is_active", 1)])

        # Form submission indexes
        self._db.form_submissions.create_index([("customer_id", 1), ("created_at", -1)])
        self._db.form_submissions.create_index([("form_config_id", 1), ("created_at", -1)])
        self._db.form_submissions.create_index("opnform_submission_id", unique=True)
        self._db.form_submissions.create_index([("metadata.submitted_at", -1)])
        self._db.form_submissions.create_index("processing_status")

        # Report cache indexes
        self._db.report_cache.create_index([
            ("customer_id", 1),
            ("form_config_id", 1),
            ("report_type", 1),
            ("report_date", -1)
        ])
        self._db.report_cache.create_index("expires_at", expireAfterSeconds=0)

    def close(self):
        if self._client:
            self._client.close()
            self._client = None
            self._db = None

# Singleton instance
mongodb = MongoDBConnection()
```

#### Component 3: Webhook Signature Validator
**File**: `src/infrastructure/api/middleware/opnform_webhook_validator.py`

```python
import hmac
import hashlib
from typing import Optional
from flask import Request

class OpnFormWebhookValidator:
    @staticmethod
    def validate_signature(
        request: Request,
        webhook_secret: str
    ) -> bool:
        """
        Validates OpnForm webhook signature using HMAC-SHA256

        OpnForm sends signature in header: X-OpnForm-Signature: sha256=<signature>
        We need to compute HMAC-SHA256 of raw request body with webhook secret
        """
        signature_header = request.headers.get("X-OpnForm-Signature", "")

        if not signature_header.startswith("sha256="):
            return False

        received_signature = signature_header[7:]  # Remove "sha256=" prefix

        # Get raw request body (IMPORTANT: use raw bytes, not parsed JSON)
        raw_body = request.get_data()

        # Compute expected signature
        expected_signature = hmac.new(
            webhook_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256
        ).hexdigest()

        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(received_signature, expected_signature)
```

#### Component 4: Webhook Receiver Endpoint
**File**: `src/infrastructure/api/routes/webhook_routes.py`

```python
from flask import Blueprint, request, jsonify
from src.infrastructure.persistence.mongodb.connection import mongodb
from src.infrastructure.api.middleware.opnform_webhook_validator import OpnFormWebhookValidator
from src.application.use_cases.process_webhook_submission_use_case import ProcessWebhookSubmissionUseCase
from bson import ObjectId
import logging

webhook_bp = Blueprint("webhook", __name__)
logger = logging.getLogger(__name__)

@webhook_bp.route("/webhook/<customer_id>", methods=["POST"])
def receive_webhook(customer_id: str):
    """
    Receives webhook from OpnForm when a form is submitted

    Security:
    1. Validates customer_id exists
    2. Validates HMAC signature
    3. Stores submission in MongoDB
    4. Returns 200 OK to OpnForm
    """
    try:
        # Validate customer exists
        db = mongodb.connect()
        customer = db.customers.find_one({"_id": ObjectId(customer_id)})

        if not customer:
            logger.warning(f"Webhook received for unknown customer: {customer_id}")
            return jsonify({"error": "Customer not found"}), 404

        if customer.get("status") != "active":
            logger.warning(f"Webhook received for inactive customer: {customer_id}")
            return jsonify({"error": "Customer inactive"}), 403

        # Validate webhook signature
        webhook_secret = customer.get("webhook_secret")
        if not OpnFormWebhookValidator.validate_signature(request, webhook_secret):
            logger.error(f"Invalid webhook signature for customer: {customer_id}")
            return jsonify({"error": "Invalid signature"}), 401

        # Parse webhook payload
        payload = request.get_json()

        # Process submission asynchronously (use case pattern)
        use_case = ProcessWebhookSubmissionUseCase(db)
        submission_id = use_case.execute(customer_id, payload)

        logger.info(f"Webhook processed successfully: {submission_id}")

        # Return 200 OK to OpnForm
        return jsonify({
            "status": "success",
            "submission_id": str(submission_id)
        }), 200

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        # Still return 200 to OpnForm to prevent retries
        # Store error internally for later review
        return jsonify({
            "status": "accepted",
            "message": "Webhook received, processing in background"
        }), 200
```

#### Component 5: Telegram Bot Handler for Reports
**File**: `src/presentation/handlers/opnform_report_handler.py`

```python
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from src.application.use_cases.get_daily_report_use_case import GetDailyReportUseCase
from src.application.use_cases.get_monthly_report_use_case import GetMonthlyReportUseCase
from src.infrastructure.persistence.mongodb.connection import mongodb
from datetime import datetime, date

async def daily_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /daily_report command"""
    user_id = str(update.effective_user.id)
    chat_id = str(update.effective_chat.id)

    # Get customer from MongoDB
    db = mongodb.connect()
    customer = db.customers.find_one({"telegram_user_id": user_id})

    if not customer:
        await update.message.reply_text(
            "❌ You are not registered. Please contact admin to register."
        )
        return

    # Get today's report
    use_case = GetDailyReportUseCase(db)
    report = use_case.execute(str(customer["_id"]), date.today())

    # Format report message
    message = format_daily_report(report)

    await update.message.reply_text(message, parse_mode="Markdown")

async def monthly_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /monthly_report command"""
    user_id = str(update.effective_user.id)

    # Show month selector
    keyboard = [
        [
            InlineKeyboardButton("January", callback_data="month_report:2025-01"),
            InlineKeyboardButton("February", callback_data="month_report:2025-02"),
            InlineKeyboardButton("March", callback_data="month_report:2025-03")
        ],
        # ... more months
        [
            InlineKeyboardButton("December", callback_data="month_report:2025-12")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📅 Select month for report:",
        reply_markup=reply_markup
    )

async def month_report_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle month selection callback"""
    query = update.callback_query
    await query.answer()

    user_id = str(update.effective_user.id)
    month_str = query.data.split(":")[1]  # e.g., "2025-12"

    # Get customer from MongoDB
    db = mongodb.connect()
    customer = db.customers.find_one({"telegram_user_id": user_id})

    if not customer:
        await query.edit_message_text("❌ You are not registered.")
        return

    # Get monthly report
    use_case = GetMonthlyReportUseCase(db)
    year, month = map(int, month_str.split("-"))
    report = use_case.execute(str(customer["_id"]), year, month)

    # Format report message
    message = format_monthly_report(report, year, month)

    await query.edit_message_text(message, parse_mode="Markdown")

def format_daily_report(report: dict) -> str:
    """Format daily report for Telegram"""
    message = f"📊 *Daily Report* - {report['date']}\n\n"

    for form in report.get("forms", []):
        message += f"📝 *{form['name']}*\n"
        message += f"   Submissions: {form['count']}\n"

        # Add summary statistics
        if form.get("summary"):
            for key, value in form["summary"].items():
                message += f"   • {key}: {value}\n"

        message += "\n"

    total = sum(f["count"] for f in report.get("forms", []))
    message += f"*Total Submissions:* {total}"

    return message

def format_monthly_report(report: dict, year: int, month: int) -> str:
    """Format monthly report for Telegram"""
    from calendar import month_name

    message = f"📊 *Monthly Report* - {month_name[month]} {year}\n\n"

    for form in report.get("forms", []):
        message += f"📝 *{form['name']}*\n"
        message += f"   Total Submissions: {form['total_count']}\n"
        message += f"   Average per day: {form['avg_per_day']:.1f}\n"
        message += f"   Most active day: {form['most_active_day']}\n\n"

    total = sum(f["total_count"] for f in report.get("forms", []))
    message += f"*Total Submissions:* {total}"

    return message

# Register handlers
def register_opnform_report_handlers(application):
    application.add_handler(CommandHandler("daily_report", daily_report_command))
    application.add_handler(CommandHandler("monthly_report", monthly_report_command))
    application.add_handler(CallbackQueryHandler(
        month_report_callback,
        pattern="^month_report:"
    ))
```

### 8.5 Telegram MiniApp Integration

**Option 1: Embedded OpnForm (iFrame)**
```html
<!-- Telegram MiniApp HTML -->
<!DOCTYPE html>
<html>
<head>
    <title>Daily Form</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
</head>
<body>
    <iframe
        src="https://form.opnform.com/your-form-slug"
        width="100%"
        height="100%"
        frameborder="0"
        allowfullscreen>
    </iframe>

    <script>
        // Initialize Telegram Web App
        let tg = window.Telegram.WebApp;
        tg.expand();

        // Listen for form submission success
        window.addEventListener('message', function(event) {
            if (event.data.type === 'form-submitted') {
                tg.showAlert('Form submitted successfully!');
                tg.close();
            }
        });
    </script>
</body>
</html>
```

**Option 2: Direct Link Button**
```python
# In Telegram bot
keyboard = [
    [InlineKeyboardButton("Fill Daily Form",
                         url="https://form.opnform.com/daily-operation-notes")]
]
reply_markup = InlineKeyboardMarkup(keyboard)
await update.message.reply_text(
    "Click below to fill today's form:",
    reply_markup=reply_markup
)
```

**Option 3: Custom MiniApp with OpnForm Embed**
- Build custom MiniApp UI
- Fetch form fields from OpnForm API
- Render form in MiniApp
- Submit directly to OpnForm API
- Receive webhook on submission

---

## 9. Security Considerations

### 9.1 Admin Portal Security

**Authentication:**
- Telegram Login Widget with HMAC-SHA256 verification
- Admin whitelist (environment variable or database)
- JWT tokens with short expiration (8 hours access, 30 days refresh)
- HttpOnly cookies for token storage (optional, more secure than localStorage)
- Automatic token refresh mechanism

**Authorization:**
- Role-based access control (future: super admin vs admin)
- API endpoints protected with `@jwt_required` decorator
- Customer-level data isolation

**Security Headers:**
- CORS configuration (whitelist admin portal domain)
- Content Security Policy (CSP)
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff

**Rate Limiting:**
- Login endpoint: 5 attempts per 15 minutes per IP
- API endpoints: 100 requests per minute per user
- Webhook logs endpoint: 50 requests per minute

### 9.2 Webhook Security (Critical)

**HMAC Signature Validation**:
- **Algorithm**: HMAC-SHA256
- **Secret**: Generated per customer (32-byte random string)
- **Header**: `X-OpnForm-Signature: sha256=<hex_digest>`
- **Validation**: Constant-time comparison to prevent timing attacks
- **Failure Handling**: Log and reject (401 Unauthorized)

**Additional Security Measures**:
1. **HTTPS Only**: Webhook URLs must use HTTPS
2. **IP Whitelisting** (optional): Restrict to OpnForm's IP ranges
3. **Rate Limiting**: Prevent DoS attacks on webhook endpoint
4. **Request Body Validation**: Validate JSON schema before processing
5. **Idempotency**: Check `opnform_submission_id` to prevent duplicate processing

### 9.3 Data Privacy

**Customer Isolation**:
- Each customer has unique `customer_id`
- MongoDB queries always filter by `customer_id`
- No cross-customer data access

**Data Retention**:
- Configure TTL indexes on `form_submissions` (e.g., 1 year)
- GDPR compliance: Add "delete my data" functionality
- Export functionality for data portability

### 9.4 Authentication & Authorization

**Telegram Bot Commands**:
- Verify user is registered customer
- Check user belongs to customer's Telegram group
- Admin-only commands: `/register_opnform`, `/link_form`

**API Endpoints**:
- Reuse existing Telegram Web App auth (HMAC-SHA256)
- Add customer-level authorization checks
- Webhook endpoints: Signature validation only

---

## 10. Deployment Architecture

### 10.1 Infrastructure Requirements

**Database Servers**:
```
┌─────────────────────────────────────┐
│         MySQL Server (Existing)     │
│  - Employees, groups, check-ins     │
│  - Vehicle operations, salary       │
│  - Port: 3306                       │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         MongoDB Server (New)        │
│  - Form submissions, customers      │
│  - Form configurations, reports     │
│  - Port: 27017                      │
│  - Replica set (for production)     │
└─────────────────────────────────────┘
```

**Application Servers**:
```
┌─────────────────────────────────────┐
│       CheckIn Bot Process           │
│  - Existing functionality           │
│  - New: OpnForm report commands     │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│       Balance Bot Process           │
│  - Existing functionality           │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│       Flask API Server              │
│  - Existing: Check-in, employee API │
│  - New: Webhook receiver            │
│  - New: Admin portal API            │
│  - New: Authentication endpoints    │
│  - Port: 5000 (proxied via nginx)   │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│       Admin Portal (Static SPA)     │
│  - Vue 3 compiled assets            │
│  - Served via Nginx                 │
│  - Port: 3000 (or subdomain)        │
└─────────────────────────────────────┘
```

### 10.2 Environment Variables

```bash
# Existing
CHECKIN_BOT_TOKEN=xxx
BALANCE_BOT_TOKEN=xxx
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=xxx
DB_NAME=office_automation
API_HOST=0.0.0.0
API_PORT=5000

# New - MongoDB
MONGODB_URL=mongodb://localhost:27017/
MONGODB_DATABASE=office_automation_forms
MONGODB_MAX_POOL_SIZE=10

# New - OpnForm
OPNFORM_WEBHOOK_BASE_URL=https://yourdomain.com
OPNFORM_API_BASE_URL=https://api.opnform.com
OPNFORM_API_TOKEN=xxx  # Optional: for API calls to OpnForm

# New - Admin Portal
JWT_SECRET_KEY=xxx                 # Secret for signing JWT tokens
JWT_ACCESS_TOKEN_EXPIRES=28800     # 8 hours in seconds
JWT_REFRESH_TOKEN_EXPIRES=2592000  # 30 days in seconds
ADMIN_TELEGRAM_IDS=123456789,987654321  # Comma-separated admin Telegram IDs
ADMIN_PORTAL_URL=https://admin.yourdomain.com
CORS_ALLOWED_ORIGINS=https://admin.yourdomain.com

# New - Feature Flags
OPNFORM_FEATURE_ENABLED=true
OPNFORM_WEBHOOK_RATE_LIMIT=100  # requests per minute
```

### 10.3 Docker Compose (Updated)

```yaml
version: '3.8'

services:
   mysql:
      image: mysql:8
      environment:
         MYSQL_ROOT_PASSWORD: ${DB_PASSWORD}
         MYSQL_DATABASE: ${DB_NAME}
      volumes:
         - mysql_data:/var/lib/mysql
      ports:
         - "3306:3306"

   mongodb:
      image: mongo:7
      environment:
         MONGO_INITDB_DATABASE: ${MONGODB_DATABASE}
      volumes:
         - mongo_data:/data/db
      ports:
         - "27017:27017"

   checkin_bot:
      build: ..
      command: python -m src.infrastructure.telegram.bot_app
      env_file: ../.env
      depends_on:
         - mysql
         - mongodb

   balance_bot:
      build: ..
      command: python -m src.infrastructure.telegram.balance_bot_app
      env_file: ../.env
      depends_on:
         - mysql

   flask_api:
      build: ..
      command: python -m src.infrastructure.api.flask_app
      env_file: ../.env
      ports:
         - "5000:5000"
      depends_on:
         - mysql
         - mongodb

volumes:
   mysql_data:
   mongo_data:
```

---

## 11. Implementation Phases

### Phase 1: Foundation (Week 1-2)
**Tasks**:
- [ ] Set up MongoDB connection and repositories
- [ ] Create domain entities for Customer, FormConfiguration, FormSubmission
- [ ] Implement MongoDB repository interfaces
- [ ] Add configuration settings for MongoDB and OpnForm
- [ ] Write unit tests for repositories

**Deliverables**:
- MongoDB connection manager
- Repository implementations
- Unit tests (>80% coverage)

### Phase 2: Webhook Infrastructure (Week 2-3)
**Tasks**:
- [ ] Implement OpnForm webhook signature validator
- [ ] Create webhook receiver endpoint (`POST /webhook/<customer_id>`)
- [ ] Implement ProcessWebhookSubmissionUseCase
- [ ] Add error handling and logging
- [ ] Test webhook with OpnForm test submissions

**Deliverables**:
- Webhook endpoint with HMAC validation
- Submission processing use case
- Integration test suite

### Phase 3: Admin Portal Foundation (Week 3-4)
**Tasks**:
- [ ] Set up Vue 3 project with Vite and TypeScript
- [ ] Install and configure UI library (Element Plus)
- [ ] Set up Vue Router and Pinia stores
- [ ] Create layout components (Header, Sidebar, Footer)
- [ ] Implement Telegram Login Widget integration
- [ ] Build authentication flow (login, logout, token management)
- [ ] Create Flask authentication endpoints (JWT)
- [ ] Set up Axios service with interceptors
- [ ] Implement CORS and security headers

**Deliverables**:
- Admin portal shell with authentication
- Protected routes and navigation
- JWT token management
- Login/logout flow working

### Phase 4: Customer & Form Management (Week 4-5)
**Tasks**:
- [ ] Build Customer List view with table and filters
- [ ] Create Customer Form component (create/edit)
- [ ] Implement Customer Details view
- [ ] Build Form Link Wizard component
- [ ] Create Field Mapping UI
- [ ] Implement RegisterOpnFormCustomerUseCase (backend)
- [ ] Create LinkFormConfigurationUseCase (backend)
- [ ] Build all customer/form API endpoints
- [ ] Add form/customer CRUD operations in admin portal
- [ ] Implement webhook URL/secret copy functionality

**Deliverables**:
- Complete customer onboarding flow via admin portal
- Form linking and management UI
- Customer/form API endpoints
- Alternative: Telegram bot commands for onboarding

### Phase 5: Webhook Logs & Analytics (Week 5-6)
**Tasks**:
- [ ] Build Webhook Logs Viewer component
- [ ] Implement real-time log filtering and search
- [ ] Create webhook log detail modal
- [ ] Build Analytics Dashboard view
- [ ] Implement submission charts (Chart.js/ECharts)
- [ ] Create customer rankings component
- [ ] Build form usage statistics
- [ ] Implement webhook logs API endpoint
- [ ] Create analytics/statistics API endpoints
- [ ] Add export functionality (CSV/JSON)

**Deliverables**:
- Webhook logs viewer with filters
- Analytics dashboard with charts
- Export tools
- Real-time monitoring capability

### Phase 6: Reporting System (Week 6-7)
**Tasks**:
- [ ] Implement GetDailyReportUseCase with MongoDB aggregation
- [ ] Implement GetMonthlyReportUseCase
- [ ] Add report caching mechanism
- [ ] Create `/daily_report` and `/monthly_report` bot commands
- [ ] Build report formatters for Telegram
- [ ] Add reports section to admin portal (optional)
- [ ] Implement report export (PDF, CSV)

**Deliverables**:
- Daily and monthly report generation
- Telegram bot report commands
- Report caching system
- Report viewing in admin portal

### Phase 7: MiniApp Integration (Week 7-8)
**Tasks**:
- [ ] Build Telegram MiniApp for form list
- [ ] Implement form submission UI (or iFrame embed)
- [ ] Add success/error notifications
- [ ] Integrate with existing auth system
- [ ] Test MiniApp on iOS and Android Telegram

**Deliverables**:
- Telegram MiniApp for form access
- User-friendly submission flow
- Mobile testing report

### Phase 8: Testing & Optimization (Week 8-9)
**Tasks**:
- [ ] Unit tests for backend (repositories, use cases, validators)
- [ ] Integration tests for webhook flow
- [ ] Frontend component tests (Vue Test Utils)
- [ ] End-to-end tests (Cypress or Playwright)
- [ ] Load testing on webhook endpoint (1000 submissions/hour)
- [ ] MongoDB query optimization (indexes, query times)
- [ ] Admin portal performance optimization (lazy loading, code splitting)
- [ ] Security audit (webhook validation, JWT, CORS, rate limiting)
- [ ] Documentation (API docs, admin guide, developer guide)

**Deliverables**:
- Comprehensive test suite (>80% coverage)
- Performance test results
- Security audit report
- Complete documentation

### Phase 9: Deployment & Monitoring (Week 9-10)
**Tasks**:
- [ ] Set up MongoDB production server (replica set)
- [ ] Build admin portal for production (`npm run build`)
- [ ] Configure Nginx for admin portal and API proxy
- [ ] Set up SSL certificates (Let's Encrypt)
- [ ] Configure monitoring (MongoDB Atlas, Grafana, or similar)
- [ ] Set up application monitoring (Sentry for error tracking)
- [ ] Configure alerts (submission failures, webhook errors, API errors)
- [ ] Deploy admin portal to production
- [ ] Deploy backend updates to production
- [ ] Train admin team on using admin portal
- [ ] Create admin user guide and video tutorials

**Deliverables**:
- Production deployment (backend + admin portal)
- Monitoring and alerting dashboard
- Admin training materials
- User guide and documentation

**Updated Timeline:**
- Phase 1: Foundation (Week 1-2)
- Phase 2: Webhooks (Week 2-3)
- Phase 3: Admin Portal Foundation (Week 3-4)
- Phase 4: Customer & Form Management (Week 4-5)
- Phase 5: Webhook Logs & Analytics (Week 5-6)
- Phase 6: Reporting (Week 6-7)
- Phase 7: MiniApp (Week 7-8)
- Phase 8: Testing (Week 8-9)
- Phase 9: Deployment (Week 9-10)

**Total Estimated Time:** 10 weeks with admin portal (vs 7-8 weeks Telegram-only)

---

## 12. Testing Strategy

### 12.1 Backend Unit Tests

**Coverage Target**: >80%

**Test Suites**:
1. **Repository Tests**: Mock MongoDB, test CRUD operations
2. **Use Case Tests**: Mock repositories, test business logic
3. **Validator Tests**: Test HMAC signature validation with known inputs
4. **Report Generator Tests**: Test aggregation logic with sample data

**Example Test**:
```python
import unittest
from src.infrastructure.api.middleware.opnform_webhook_validator import OpnFormWebhookValidator
from unittest.mock import MagicMock

class TestOpnFormWebhookValidator(unittest.TestCase):
    def test_valid_signature(self):
        # Create mock request
        request = MagicMock()
        request.headers.get.return_value = "sha256=abc123..."
        request.get_data.return_value = b'{"test": "data"}'

        # Test validation
        result = OpnFormWebhookValidator.validate_signature(
            request,
            "test_secret"
        )

        self.assertTrue(result)

    def test_invalid_signature(self):
        # Test with wrong signature
        # Assert False returned
        pass
```

### 12.2 Frontend Unit Tests (Vue Components)

**Coverage Target:** >70%

**Test Suites:**
1. **Component Tests**: Test Vue components in isolation
2. **Store Tests**: Test Pinia state management
3. **Service Tests**: Test API service functions
4. **Utility Tests**: Test helper functions

**Tools:**
- Vitest (test runner)
- Vue Test Utils (component testing)
- MSW (Mock Service Worker for API mocking)

**Example Test:**
```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import CustomerList from '@/components/customers/CustomerList.vue'

describe('CustomerList', () => {
  it('renders customer data correctly', () => {
    const customers = [
      { id: '1', business_name: 'ABC Corp', status: 'active' }
    ]

    const wrapper = mount(CustomerList, {
      props: { customers }
    })

    expect(wrapper.text()).toContain('ABC Corp')
    expect(wrapper.find('.status-badge').text()).toBe('active')
  })
})
```

### 12.3 Integration Tests

**Backend Integration Tests:**
1. **End-to-End Webhook Flow**:
   - Send webhook POST → Validate signature → Save to MongoDB → Verify saved
2. **Customer Onboarding Flow**:
   - Register customer → Create webhook → Link form → Submit test form
3. **Report Generation**:
   - Insert test submissions → Generate report → Verify calculations
4. **Authentication Flow**:
   - Telegram login → JWT token → Access protected endpoints

**Frontend Integration Tests (E2E):**
1. **Admin Login Flow**:
   - Click Telegram login → Mock auth → Verify dashboard loads
2. **Customer Registration**:
   - Fill form → Submit → Verify customer appears in list
3. **Form Linking**:
   - Navigate to customer → Click link form → Fill wizard → Verify success
4. **Webhook Logs**:
   - View logs → Apply filters → Verify results update

**Tools**:
- Backend: `pytest`, `mongomock`, `testcontainers`
- Frontend: Cypress or Playwright for E2E tests

### 12.4 Load Testing

**Scenarios**:
1. **Webhook Endpoint**: 1000 concurrent submissions
2. **Admin Portal API**: 100 concurrent admin requests
3. **Report Generation**: 50 concurrent report requests
4. **MongoDB Queries**: Measure query times with 1M+ submissions
5. **Admin Portal UI**: Lighthouse performance audit

**Tools**:
- Backend: `locust` or `k6` for load testing
- Frontend: Lighthouse, WebPageTest
- Database: MongoDB profiler for query analysis

---

## 13. Monitoring & Observability

### 13.1 Metrics to Track

**Backend Metrics**:
- Webhook requests per minute (by customer)
- Webhook validation success/failure rate
- Submission processing time (p50, p95, p99)
- Report generation time
- MongoDB query times
- API response times (admin endpoints)
- Authentication success/failure rates

**Database Metrics**:
- MongoDB connection pool usage
- Document insert rate
- Index hit ratio
- Storage size per collection

**Frontend Metrics** (Admin Portal):
- Page load times
- JavaScript bundle size
- API request latency from client
- User session duration
- Feature usage (which pages visited most)
- Error rates (client-side errors)

**Business Metrics**:
- Total customers onboarded
- Total forms configured
- Total submissions per day/month
- Most active customers
- Average submissions per customer

### 13.2 Logging Strategy

**Log Levels**:
- **DEBUG**: Detailed request/response data
- **INFO**: Successful operations (webhook received, submission processed)
- **WARNING**: Invalid signatures, rate limit hits
- **ERROR**: Processing failures, database errors
- **CRITICAL**: System failures, data corruption

**Log Format** (JSON):
```json
{
  "timestamp": "2025-12-11T10:30:00Z",
  "level": "INFO",
  "component": "webhook_receiver",
  "customer_id": "507f1f77bcf86cd799439011",
  "form_id": "opnform_form_123",
  "submission_id": "sub_456",
  "message": "Webhook processed successfully",
  "duration_ms": 45
}
```

**Frontend Error Tracking:**
- Use Sentry or similar for JavaScript errors
- Track failed API calls from admin portal
- Monitor Vue routing errors
- Track authentication failures

### 13.3 Alerting Rules

**Critical Alerts** (PagerDuty, Slack):
- Webhook endpoint down (5xx errors >10 in 5 minutes)
- Admin portal API down (5xx errors >10 in 5 minutes)
- MongoDB connection failures
- Signature validation failures >50% in 10 minutes
- Authentication service down

**Warning Alerts** (Slack):
- Submission processing taking >5 seconds
- MongoDB query slow (>1 second)
- Webhook rate limit hits
- Admin portal API response time >2 seconds
- High JavaScript error rate in admin portal (>10 errors/minute)

---

## 14. Cost Estimation

### 14.1 Infrastructure Costs

**MongoDB Hosting** (MongoDB Atlas):
- **M10 Cluster** (Shared): $57/month
  - 10GB storage, 2GB RAM
  - Suitable for <100k submissions/month
- **M30 Cluster** (Dedicated): $312/month
  - 40GB storage, 8GB RAM
  - Suitable for 100k-1M submissions/month

**OpnForm Subscription**:
- **Pro Plan**: $29/month (webhook feature required)
- **Team Plan**: $99/month (for multiple workspace admins)

**Admin Portal Hosting**:
- **Option 1**: Self-hosted (included in existing server costs)
- **Option 2**: Vercel/Netlify free tier (adequate for admin portal)
- **Option 3**: AWS S3 + CloudFront: ~$5-10/month

**Monitoring Tools** (Optional):
- Sentry (error tracking): Free tier or $26/month
- Uptime monitoring: Free (UptimeRobot) or $7/month

**Total Monthly Cost** (Estimate):
- Small deployment: ~$90/month (M10 + Pro + free hosting)
- Medium deployment: ~$365/month (M30 + Team + paid hosting + monitoring)

### 14.2 Development Cost

**Estimated Effort**: 10 weeks (1 full-stack developer) or 8 weeks (1 backend + 1 frontend developer)

**Breakdown** (Single Developer):
- Phase 1 (Foundation): 80 hours
- Phase 2 (Webhooks): 80 hours
- Phase 3 (Admin Portal Foundation): 60 hours
- Phase 4 (Customer/Form Management): 80 hours
- Phase 5 (Logs & Analytics): 80 hours
- Phase 6 (Reporting): 60 hours
- Phase 7 (MiniApp): 40 hours
- Phase 8 (Testing): 80 hours
- Phase 9 (Deployment): 40 hours
- **Total**: 600 hours (~15 weeks at 40 hours/week, or 10 weeks at 60 hours/week)

**Cost Savings vs Custom Development:**
- Using OpnForm saves ~200 hours of form builder development
- Admin portal adds ~140 hours vs Telegram-only approach
- Net additional time: 140 hours for significantly better UX

---

## 15. Risk Assessment & Mitigation

### 15.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| OpnForm webhook changes breaking signature validation | High | Low | Pin to specific OpnForm webhook version, monitor changelog |
| MongoDB performance degradation with large datasets | High | Medium | Implement proper indexes, use aggregation pipeline, add caching |
| Webhook endpoint DDoS | Medium | Medium | Rate limiting, CAPTCHA on form submit, IP whitelisting |
| Data loss due to MongoDB failure | High | Low | Use replica set, automated backups, test restore process |
| Form schema changes breaking reports | Medium | High | Use flexible schema, validate fields, add migration process |
| Admin portal XSS/CSRF vulnerabilities | High | Low | Input sanitization, CSP headers, CSRF tokens |
| JWT token theft | Medium | Low | Short expiration, HttpOnly cookies, token rotation |

### 15.2 Business Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Customer creates too many forms (cost overhead) | Medium | Medium | Implement form limits per package level |
| OpnForm pricing changes | Medium | Low | Negotiate annual contract, plan for self-hosted OpnForm option |
| Customers prefer custom forms over OpnForm | Low | Medium | Offer hybrid solution (custom forms + OpnForm) |
| Low customer adoption | High | Medium | Provide onboarding support, create video tutorials, offer free trial |

### 15.3 Compliance Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| GDPR violations (data retention) | High | Low | Implement TTL indexes, add data export/delete features |
| Data breach (customer form data exposed) | Critical | Low | HTTPS only, signature validation, encryption at rest |
| Audit trail missing | Medium | Low | Log all operations, immutable audit log collection |

---

## 16. Future Enhancements

### Phase 2 Features (Post-MVP)

1. **Admin Portal Enhancements**:
   - Real-time webhook log streaming (WebSockets)
   - Drag-and-drop dashboard customization
   - Customer impersonation mode (view as customer)
   - Bulk operations (multi-select, batch actions)
   - Advanced filtering and saved views
   - Dark mode toggle

2. **Advanced Reporting**:
   - Custom date range reports
   - Field-level analytics (e.g., "Most common operation type")
   - Visualizations (charts, graphs)
   - Scheduled reports (daily email digest)

3. **Form Templates**:
   - Pre-built form templates for common use cases
   - One-click form duplication
   - Form versioning

4. **Multi-Language Support**:
   - Internationalize bot commands (English, Khmer, etc.)
   - Form field translation support

5. **Advanced Integrations**:
   - Google Sheets export (like Balance Bot)
   - PDF report generation
   - Zapier/Make.com integration
   - Slack notifications

6. **Self-Hosted OpnForm**:
   - Deploy OpnForm instance for full control
   - Custom branding
   - No per-form subscription costs

7. **Mobile App**:
   - Native iOS/Android app for form filling
   - Offline submission support
   - Push notifications

8. **AI/ML Features**:
   - Anomaly detection (unusual submission patterns)
   - Auto-categorization of text responses
   - Predictive analytics (forecast future submissions)

---

## 17. Success Metrics

### Launch Metrics (First 3 Months)

**Adoption**:
- Target: 10 customers onboarded
- Target: 20+ forms configured
- Target: 1000+ submissions received

**Performance**:
- Webhook processing time: <500ms (p95)
- Admin portal page load: <2 seconds
- API response time: <300ms (p95)
- Report generation time: <2 seconds
- System uptime: >99.5%

**Admin Portal Usage**:
- Daily active admins: >80% of admin team
- Average session duration: >5 minutes
- Customer onboarding time: <10 minutes per customer

**User Satisfaction**:
- Customer feedback score: >4/5
- Support tickets: <5 per month
- Feature requests collected: Track in feedback system

### Long-Term Metrics (6+ Months)

**Scale**:
- 50+ customers
- 100+ forms
- 10,000+ submissions/month

**Engagement**:
- Daily active users: >30% of customers
- Average submissions per customer: >100/month
- Report generation frequency: >5 times/week per customer

---

## 18. Documentation Deliverables

### Technical Documentation

1. **API Documentation** (OpenAPI/Swagger):
   - All new endpoints documented
   - Request/response examples
   - Authentication requirements
   - Error codes

2. **Architecture Diagrams**:
   - System architecture overview
   - Data flow diagrams
   - Sequence diagrams for key flows
   - MongoDB schema diagrams

3. **Developer Guide**:
   - Local development setup (backend + frontend)
   - Running backend and frontend dev servers
   - Building admin portal for production
   - Running tests (backend + frontend)
   - Debugging tips (Vue DevTools, Flask debugging)
   - Contributing guidelines

### User Documentation

1. **Admin Guide**:
   - How to log into admin portal
   - How to register new customers
   - How to link forms to customers
   - How to view webhook logs and troubleshoot issues
   - How to generate and export reports
   - How to monitor system health
   - How to manage customer subscriptions

2. **Customer Guide** (for end customers):
   - How to create forms in OpnForm
   - How to configure webhooks
   - How to view reports in Telegram
   - FAQ and troubleshooting

3. **Video Tutorials**:
   - Admin portal overview and navigation (5 min)
   - Registering a customer via admin portal (5 min)
   - Linking an OpnForm form (7 min)
   - Viewing webhook logs and troubleshooting (5 min)
   - Generating and analyzing reports (8 min)
   - Customer: Creating your first form in OpnForm (10 min)

---

## 19. Conclusion

This blueprint provides a comprehensive plan for integrating OpnForm with your Telegram-based office automation system. The solution enables zero-code customer onboarding while maintaining security, scalability, and flexibility.

**Key Advantages**:
- ✅ Zero code changes per customer (self-service onboarding)
- ✅ Modern admin portal (Vue 3 SPA with professional UI)
- ✅ Flexible form creation (customers control their forms via OpnForm)
- ✅ Secure webhook handling (HMAC signature validation)
- ✅ Secure admin authentication (Telegram Login + JWT)
- ✅ Real-time monitoring (webhook logs, analytics dashboard)
- ✅ Scalable architecture (MongoDB for JSON data)
- ✅ Comprehensive reporting (daily/monthly via bot and admin portal)
- ✅ Maintains existing system (MySQL unchanged, non-disruptive integration)

**Next Steps**:
1. Review and approve this blueprint
2. Set up development environment (MongoDB instance)
3. Begin Phase 1 implementation (Foundation)
4. Schedule weekly progress reviews
5. Plan production deployment timeline

---

## Appendix A: Useful Resources

### Documentation Links
- [OpnForm Technical Docs](https://docs.opnform.com/api-reference/introduction)
- [OpnForm Webhook Security](https://docs.opnform.com/api-reference/integrations/webhook-security)
- [OpnForm Help Center](https://help.opnform.com/en/article/can-i-trigger-another-service-whenever-my-form-receives-a-submission-webhooks-6nrnfn/)
- [MongoDB Python Driver](https://pymongo.readthedocs.io/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Telegram Web Apps](https://core.telegram.org/bots/webapps)

### GitHub Repositories
- [OpnForm GitHub](https://github.com/JhumanJ/OpnForm)
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [pymongo](https://github.com/mongodb/mongo-python-driver)

---

**Document Version**: 1.0
**Last Updated**: December 11, 2025
**Author**: Claude Code Blueprint Generator
**Status**: Draft - Awaiting Review