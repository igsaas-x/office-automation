# Telegram Authentication & Validation Filter - Design Blueprint

## 1. Overview

### Purpose
Implement a **mandatory global filter** that validates ALL incoming API requests to ensure they originate from authenticated Telegram users with valid user details in our system.

**Security Requirement**: NO anonymous API calls allowed. All `/api/*` endpoints must pass through authentication to prevent unauthorized access and attacks.

### Scope
- **Flask API Layer ONLY**: Validate HTTP requests from Telegram Mini App (Web App) to `/api/*` endpoints
- **User Verification**: Cross-reference against registered employees in database
- **Out of Scope**: Telegram bot messages (bot handles its own validation)

### Critical Design Principle
**Zero-Trust API Access**: Every API request must provide valid Telegram authentication. The only exceptions are non-sensitive endpoints (`/health`, `/api-docs`) that contain no business logic or data.

---

## 2. Current State Analysis

### Existing Infrastructure
- **Framework**: Flask 3.0.0 + python-telegram-bot 22.5
- **CORS**: Already configured for `https://web.telegram.org` and `https://t.me`
- **Architecture**: Clean architecture with domain/application/infrastructure separation
- **Authentication**: None (currently relies on implicit trust of telegram_user_id)

### Security Gaps (Current Vulnerabilities)
1. **Anonymous API Access**: Anyone can call API endpoints without authentication
2. **User ID Spoofing**: No validation that `telegram_user_id` matches real Telegram users
3. **No Authorization**: No check that user exists in our `employees` table before processing
4. **Missing Signature Verification**: No verification of Telegram Web App initData authenticity
5. **No Rate Limiting**: API can be abused with unlimited requests (DoS vulnerability)
6. **Implicit Trust**: Group chat validation is implicit, not explicit

**Risk Level**: HIGH - System is vulnerable to:
- Unauthorized data access
- Data manipulation by anonymous users
- Denial of Service attacks
- Identity spoofing

---

## 3. Solution Architecture

### Flask Middleware Validation Approach

```
┌──────────────────────────────────────────────────┐
│            Telegram Mini App (Web App)           │
│                                                  │
│  User opens app in Telegram                      │
│  Telegram generates initData with signature      │
│                                                  │
└───────────────────────┬──────────────────────────┘
                        │
                        │ HTTPS POST/GET
                        │ Headers: initData, telegram_user_id
                        ▼
            ┌───────────────────────┐
            │  Flask API Server     │
            │                       │
            │  ┌─────────────────┐  │
            │  │ before_request  │  │
            │  │   Middleware    │  │
            │  │                 │  │
            │  │ 1. Parse init   │  │
            │  │ 2. Verify HMAC  │  │
            │  │ 3. Check user   │  │
            │  │ 4. Enrich ctx   │  │
            │  └────────┬────────┘  │
            │           │           │
            │           ▼           │
            │  ┌─────────────────┐  │
            │  │ Route Handlers  │  │
            │  │ /api/checkin    │  │
            │  │ /api/employees  │  │
            │  └─────────────────┘  │
            └───────────┬───────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  Database Layer       │
            │                       │
            │  - EmployeeModel      │
            │  - GroupModel         │
            │  - CheckInModel       │
            └───────────────────────┘
```

---

## 4. Component Design

### 4.1 Flask API Middleware

**Location**: `src/infrastructure/api/middleware/telegram_auth.py`

#### Responsibilities
1. **Telegram Web App Data Validation**
   - Verify `initData` signature using bot token
   - Extract and validate `user` object from initData
   - Confirm data freshness (timestamp check)

2. **User Existence Check**
   - Query `EmployeeModel` for telegram_id
   - Verify employee is active (if status field exists)
   - Cache results for performance

3. **Group Chat Validation**
   - If `group_chat_id` provided, verify against `GroupModel`
   - Ensure employee has access to specified group

4. **Request Context Enrichment**
   - Attach validated user object to Flask `g` context
   - Include employee_id, permissions, group associations

#### Enforcement Strategy
**Default Behavior**: REJECT ALL requests to `/api/*` unless:
1. Valid initData signature is present AND
2. User exists in EmployeeModel AND
3. (If applicable) Group exists in GroupModel

**Exempt Paths** (no authentication required):
- `/health` - System health check
- `/api-docs` - Swagger documentation
- `/metrics` - Monitoring metrics (if exists)

All other `/api/*` endpoints are PROTECTED by default.

#### Configuration
```
TELEGRAM_AUTH_ENABLED = True/False
TELEGRAM_AUTH_EXEMPT_PATHS = ["/health", "/api-docs", "/metrics"]
TELEGRAM_INITDATA_MAX_AGE = 3600  # seconds
TELEGRAM_AUTH_CACHE_TTL = 300  # seconds
TELEGRAM_AUTH_STRICT_MODE = True  # Reject if False, log if True
```

#### Error Responses
- `401 Unauthorized`: Missing or invalid Telegram authentication (initData)
- `403 Forbidden`: Valid Telegram user but not registered as employee
- `404 Not Found`: Referenced group_chat_id doesn't exist in database
- `429 Too Many Requests`: Rate limit exceeded

---

## 5. Validation Rules Matrix

| Request Source | Validation Type | Required Fields | Database Check | Action on Failure |
|---------------|-----------------|-----------------|----------------|-------------------|
| **POST /api/checkin** | Full + InitData | initData, telegram_user_id, group_chat_id | EmployeeModel + GroupModel | 401/403 error |
| **POST /api/employees/register** | Full + InitData | initData, telegram_id | None (creates new) | 401 error |
| **GET /api/employees/{id}/status** | Full + InitData | initData, telegram_user_id | EmployeeModel | 401/403 error |
| **GET /health** | None | - | - | Always allow |
| **GET /api-docs** | None | - | - | Always allow |
| **All other /api/*** | Full + InitData | initData | EmployeeModel | 401/403 error |

---

## 6. Telegram Web App InitData Validation

### What is InitData?
Telegram Mini Apps send a signed `initData` string containing:
- `user`: JSON object with id, first_name, last_name, username
- `auth_date`: Unix timestamp
- `hash`: HMAC-SHA256 signature

### Validation Algorithm
```
1. Parse initData query string
2. Extract 'hash' parameter
3. Sort remaining parameters alphabetically
4. Create data-check-string (key=value\n format)
5. Compute secret_key = HMAC-SHA256(bot_token, "WebAppData")
6. Compute hash = HMAC-SHA256(secret_key, data-check-string)
7. Compare computed hash with provided hash (constant-time)
8. Check auth_date is within MAX_AGE window
```

### Implementation Notes
- Use `hmac` and `hashlib` standard library
- Constant-time comparison to prevent timing attacks
- Log validation failures for security monitoring

### Pseudocode Example
```python
@app.before_request
def validate_telegram_auth():
    # 1. Check if path is exempt
    if request.path in EXEMPT_PATHS:
        return None  # Allow request to proceed

    # 2. Extract initData from request (header or body)
    init_data = request.headers.get('X-Telegram-Init-Data') or \
                request.json.get('initData')

    if not init_data:
        return jsonify({"error": "Missing Telegram authentication"}), 401

    # 3. Validate HMAC signature
    if not verify_telegram_signature(init_data, BOT_TOKEN):
        log_security_event("Invalid signature", request)
        return jsonify({"error": "Invalid Telegram authentication"}), 401

    # 4. Check timestamp freshness
    auth_date = parse_init_data(init_data).get('auth_date')
    if time.time() - auth_date > MAX_AGE:
        return jsonify({"error": "Authentication expired"}), 401

    # 5. Extract user ID and check database
    telegram_user_id = parse_init_data(init_data)['user']['id']
    employee = get_employee_by_telegram_id(telegram_user_id)  # With cache

    if not employee:
        log_security_event("Unregistered user attempt", telegram_user_id)
        return jsonify({"error": "User not registered"}), 403

    # 6. Attach to request context
    g.current_user = employee
    g.telegram_data = parse_init_data(init_data)

    # 7. Allow request to proceed to route handler
    return None
```

---

## 7. Performance Considerations

### Caching Strategy
1. **User Lookup Cache**
   - Key: `telegram_id`
   - Value: `{employee_id, is_active, groups[]}`
   - TTL: 5 minutes
   - Invalidate on employee updates

2. **Group Lookup Cache**
   - Key: `chat_id`
   - Value: `{group_id, name, authorized_users[]}`
   - TTL: 10 minutes

3. **Cache Implementation**
   - Use in-memory cache (functools.lru_cache for simple cases)
   - Consider Redis for distributed setup

### Database Query Optimization
- Index on `employees.telegram_id`
- Index on `groups.chat_id`
- Consider JOIN query for user + group validation

---

## 8. Security Considerations

### Threats Mitigated
1. **Spoofed User IDs**: InitData signature prevents tampering
2. **Unauthorized Access**: Database check ensures registration
3. **Replay Attacks**: Timestamp validation limits initData lifetime
4. **Rate Limiting**: Prevents abuse and DoS

### Threats Remaining
1. **Compromised Bot Token**: If leaked, attacker can forge initData
   - Mitigation: Rotate tokens, monitor for unusual activity
2. **Leaked telegram_id**: User could register with someone else's ID
   - Mitigation: Require admin approval for registration
3. **Side-channel attacks**: Timing attacks on hash comparison
   - Mitigation: Use constant-time comparison

### Audit Logging
Log the following events:
- Failed authentication attempts
- Rate limit violations
- Unregistered user access attempts
- Group authorization failures

---

## 9. Implementation Phases

### Phase 1: Core Middleware Implementation
**Rationale**: API endpoints are externally exposed, highest priority

**Tasks**:
1. Create `src/infrastructure/api/middleware/telegram_auth.py`
2. Implement initData signature validation (HMAC-SHA256)
3. Add user existence check against EmployeeModel
4. Add group validation against GroupModel
5. Integrate with `flask_app.py` via `@app.before_request`
6. Add configuration to `settings.py`
7. Create unit tests for validation logic

**Estimated Effort**: 1 day

---

### Phase 2: Caching & Performance Optimization
**Rationale**: Minimize database queries, improve response times

**Tasks**:
1. Implement in-memory LRU cache for user lookups
2. Add cache invalidation logic
3. Benchmark middleware overhead (<10ms target)
4. Performance testing under load
5. Add monitoring metrics (auth success rate, latency)

**Estimated Effort**: 1 day

---

### Phase 3: Rate Limiting & Security Hardening
**Rationale**: Prevent abuse and DoS attacks

**Tasks**:
1. Implement per-user rate limiting
2. Add IP-based rate limiting (optional)
3. Create audit logging for failed auth attempts
4. Set up security monitoring dashboard
5. Alert configuration for suspicious patterns

**Estimated Effort**: 1 day

---

### Phase 4: Documentation & Testing
**Rationale**: Ensure smooth adoption and maintenance

**Tasks**:
1. Write developer documentation (middleware usage, exemptions)
2. Create API consumer guide (how to send initData)
3. Security testing (forge attempts, replay attacks)
4. Integration tests with real initData
5. Load testing (1000 req/sec target)

**Estimated Effort**: 1 day

---

**Total Estimated Effort**: 4 days

---

## 10. Configuration & Feature Flags

### Environment Variables
```bash
# Feature flags
TELEGRAM_AUTH_ENABLED=true

# Security settings
TELEGRAM_INITDATA_MAX_AGE=3600  # seconds (1 hour)
TELEGRAM_RATE_LIMIT_PER_USER=20  # requests per window
TELEGRAM_RATE_LIMIT_WINDOW=60  # seconds

# Cache settings
TELEGRAM_AUTH_CACHE_ENABLED=true
TELEGRAM_AUTH_CACHE_TTL=300  # seconds (5 minutes)

# Exempt paths (comma-separated)
TELEGRAM_AUTH_EXEMPT_PATHS=/health,/api-docs,/metrics

# Bot token for signature verification
CHECKIN_BOT_TOKEN=your_bot_token_here
```

### Gradual Rollout Strategy
1. **Week 1**: Deploy with `TELEGRAM_AUTH_ENABLED=false`, log validation results
2. **Week 2**: Enable for 10% of traffic, monitor error rates
3. **Week 3**: Enable for 50% of traffic
4. **Week 4**: Enable for 100% of traffic

---

## 11. Testing Strategy

### Unit Tests
- InitData signature validation (valid/invalid/expired)
- User lookup with mocked database
- Cache hit/miss scenarios
- Rate limiting logic

### Integration Tests
- End-to-end API request with real initData
- Database lookup integration
- Full request flow from Mini App to response

### Security Tests
- Attempt to forge initData
- Test with expired timestamps
- Replay attack simulation
- Rate limit bypass attempts

### Performance Tests
- Benchmark middleware overhead (<10ms target)
- Cache effectiveness (>90% hit rate target)
- Load testing (1000 req/sec)

---

## 12. Documentation Requirements

### For Developers
- API middleware usage guide
- How to exempt endpoints from validation
- Custom filter implementation examples
- Troubleshooting common issues

### For API Consumers
- How to obtain initData from Telegram Web App
- Sample request with authentication
- Error code reference
- Rate limit guidelines

---

## 13. Migration Plan

### Backward Compatibility
- **Problem**: Existing API clients may not send initData
- **Solution**: Gradual migration with feature flag
  - Initially, log warnings for missing initData
  - After grace period, enforce strict validation

### Database Migrations
- No schema changes required
- Ensure indexes exist on `telegram_id` and `chat_id`

---

## 14. Success Metrics

### Technical Metrics
- Authentication success rate: >99%
- False positive rate: <0.1%
- Middleware latency: <10ms p99
- Cache hit rate: >90%

### Security Metrics
- Blocked unauthorized attempts: Track trend
- Zero successful spoofed requests
- Rate limit effectiveness: Blocked abuse attempts

---

## 15. Open Questions & Decisions Needed

### Questions for Team Discussion
1. **Strict vs Permissive Mode**: Should we block or just log initially during rollout?
2. **Admin Bypass**: Should admins bypass rate limits?
3. **Registration Flow**: Should `/api/employees/register` also require initData or allow anonymous registration?
4. **Exempt Endpoints**: Besides `/health` and `/api-docs`, are there other endpoints that should bypass auth?
5. **Group Authorization Model**: Should users be explicitly linked to groups in the database?

### Technical Decisions
1. **Cache Backend**: In-memory (simple) vs Redis (distributed)?
2. **Rate Limiting**: Per-user only or also per-IP?
3. **Logging Level**: What should be INFO vs WARNING vs ERROR?
4. **Error Messages**: Generic (security) vs specific (UX)?

---

## 16. References & Resources

### Telegram Documentation
- [Telegram Web Apps](https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app)
- [Bot API Security](https://core.telegram.org/bots/api#authorizing-your-bot)

### Libraries
- Flask before_request: [Flask Docs](https://flask.palletsprojects.com/en/3.0.x/api/#flask.Flask.before_request)
- Python HMAC: [Standard Library](https://docs.python.org/3/library/hmac.html)

### Security Best Practices
- OWASP Authentication Cheat Sheet
- Telegram Bot Security Guide

---

## 17. Appendix: Example Flows

### Flow A: Successful API Check-in Request
```
1. User opens Telegram Mini App
2. Telegram generates initData with HMAC signature
3. Mini App JavaScript extracts initData from window.Telegram.WebApp
4. Mini App calls POST /api/checkin with:
   - Headers: {"Content-Type": "application/json"}
   - Body: {
       "initData": "query_id=...&user=...&auth_date=...&hash=...",
       "telegram_user_id": "123456789",
       "group_chat_id": "-100987654321",
       "latitude": 13.7563,
       "longitude": 100.5018
     }
5. Flask middleware intercepts via @app.before_request
6. Middleware parses initData and validates HMAC signature ✓
7. Middleware queries EmployeeModel where telegram_id="123456789" ✓
8. Middleware queries GroupModel where chat_id="-100987654321" ✓
9. Middleware attaches employee object to flask.g.current_user
10. Request proceeds to route handler
11. Check-in record created in database
12. Response: 200 OK with check-in details
```

### Flow B: Failed Authentication - Invalid Signature
```
1. Attacker crafts malicious request to POST /api/checkin
2. Attacker modifies initData to change user.id to admin's ID
3. Flask middleware intercepts request
4. Middleware validates HMAC signature ✗ (hash doesn't match)
5. Middleware returns 401 Unauthorized
6. Response: {"error": "Invalid Telegram authentication"}
7. Request never reaches route handler
```

### Flow C: Failed Authorization - Unregistered User
```
1. User opens Mini App (valid Telegram user)
2. Telegram generates valid initData
3. User calls POST /api/checkin
4. Middleware validates initData signature ✓
5. Middleware queries EmployeeModel for telegram_id ✗ (not found)
6. Middleware returns 403 Forbidden
7. Response: {"error": "User not registered as employee"}
8. User needs to register via bot first
```

### Flow D: Rate Limit Exceeded
```
1. User makes 25 API requests in 60 seconds
2. First 20 requests succeed (under limit)
3. Request #21 triggers rate limiter
4. Middleware returns 429 Too Many Requests
5. Response: {
     "error": "Rate limit exceeded",
     "retry_after": 45  // seconds
   }
6. After 60-second window, user can make requests again
```

### Flow E: Expired InitData (Replay Attack Prevention)
```
1. User opens Mini App and gets initData at 10:00 AM
2. User closes app without making requests
3. User opens app again at 11:30 AM (90 minutes later)
4. Mini App sends cached initData with auth_date from 10:00 AM
5. Middleware checks: current_time - auth_date > MAX_AGE (3600s) ✗
6. Middleware returns 401 Unauthorized
7. Response: {"error": "Authentication expired, please refresh"}
8. Mini App must call Telegram.WebApp.close() and reopen to get fresh initData
```

---

**Document Version**: 1.1
**Last Updated**: 2025-11-16
**Status**: Draft - Ready for Review
**Owner**: Engineering Team

---

## Change Log

### v1.1 (2025-11-16)
- **Major Update**: Focused scope to Flask API middleware only (removed bot filter components)
- **Security Enhancement**: Emphasized zero-trust model - ALL API calls must be authenticated
- **Added**: Enforcement strategy section with strict default-deny approach
- **Added**: Pseudocode example for middleware implementation
- **Updated**: All example flows to focus on Mini App API requests
- **Updated**: Implementation timeline to 4 days total (1 day per phase)
- **Clarified**: Only `/health`, `/api-docs`, and `/metrics` are exempt from authentication

### v1.0 (2025-11-16)
- Initial blueprint with two-tier validation approach (API + Bot)