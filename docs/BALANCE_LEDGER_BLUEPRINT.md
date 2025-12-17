# Balance Bot - Group Expense Capture Blueprint

## Overview
- Extend the Balance bot so it can listen to group text messages, extract expense intents with an LLM (via MCP), and append structured records to the Google Sheet already used for balance reporting.
- Target outcome: fast, low-friction capture of ad-hoc expenses inside a Telegram group; if the message has only a number, the bot asks for the purpose before saving.

## Goals & Non-Goals
- Goals: detect amount-bearing messages in groups, use LLM parsing to get `{amount, currency, purpose}`, handle missing purpose with a follow-up prompt, and append to Sheets with timestamp/user/group context.
- Non-goals: redesign of balance summary rendering, historical backfill, or admin UI; support for media receipts is out of scope for this phase.

## High-Level Flow (Group Chat)
1) User posts a text message that contains at least one number.
2) Bot receives the message (MessageHandler on group chats, text only, non-command).
3) Run heuristic pre-check:
   - Extract numeric tokens and potential currency markers (៛, riel, KHR, $, USD).
   - If no purpose tokens (letters/words) beyond currency/stop words, mark `purpose_missing=True`.
4a) If purpose is present:
   - Send text to MCP LLM parser with strict schema instructions.
   - If parser returns confident result → append to Sheet → reply with success + echo.
   - If parser low confidence/invalid → ask clarifying question, then retry parse.
4b) If purpose is missing:
   - Prompt user: “Please specify expense purpose for {amount}”.
   - Store pending state (chat_id + user_id + message_id + amount + currency).
   - Next reply from same user in the chat resolves the purpose → run parser (with both amount and purpose) → append → confirm.

## Data Model for Parsed Expense (in-memory, before Sheet)
```python
ParsedExpense:
  amount_value: float          # normalized number
  currency: str                # "USD" | "KHR" | "UNKNOWN"
  purpose: str                 # short text, trimmed
  raw_text: str                # original user message
  source_chat_id: str
  source_user_id: str
  source_username: str | None
  created_at_utc: datetime
  mcp_confidence: float        # 0-1
```

## LLM Parsing Contract (Direct, In-Process)
- Client: new `ExpenseParserClient` with `parse_message(text, hints)` → `ParsedExpense | None` (no separate MCP server; runs in-process).
- Prompt requirements:
  - Return JSON only, schema: `{"amount_value": number, "currency": "USD|KHR|UNKNOWN", "purpose": "string", "confidence": 0-1}`.
  - Amount rules: if multiple amounts, pick the first clear expense; ignore counts/quantities; handle formats like `10k`, `10,000`, `10.5`, `១៥០០០` if Khmer digits appear.
  - Currency detection: `$`, `usd`, `dollar` → USD; `riel`, `៛`, `khr` → KHR; default to `UNKNOWN`.
  - Purpose rules: concise noun phrase, strip greetings/emojis.
  - If uncertain → respond `{"reason": "...", "confidence": 0}` so caller can trigger a clarification prompt.
- Transport: direct model call (e.g., OpenAI/Claude client) behind `ExpenseParserClient`; keep interface pluggable so we can swap to MCP later if needed.

## Google Sheet Write Contract
- Target Sheet: reuse `settings.BALANCE_SHEET_ID`; worksheet name always the current month (`%B`, e.g., "December").
- Append range: the month worksheet itself (no separate `Ledger` tab); create month sheet if missing and seed headers in row 1.
- Columns and format (based on provided sheet):
  1. `No` (auto-incremented row number starting at 1 beneath headers)
  2. `Date` (format like `Dec 03`, using Asia/Phnom_Penh local date)
  3. `Item` (purpose text)
  4. `Amount (USD)` (value only when currency=USD, else blank)
  5. `Amount (KHR)` (value only when currency=KHR, else blank)
- Insertion logic:
  - Find the next empty row after the header; set `No` as sequential (previous row + 1).
  - If currency is `UNKNOWN`, default to USD column (and optionally tag with “(Unknown currency)” in Item suffix to avoid losing context).
  - Preserve original ordering of entries; no sorting.
- GoogleSheetsService additions:
  - `append_expense_record(record: ParsedExpense, sheet_id: str | None = None, worksheet_name: str = "Ledger") -> str`
  - Ensure worksheet exists; auto-create with headers if not.
  - Return human-friendly reference (row number or timestamp) for confirmation messages.

## Telegram Conversation Handling
- Listener: MessageHandler on `filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND`.
- State tracking:
  - `context.chat_data["pending_expense"][user_id] = {...}` for amount-only messages.
  - Expire pending state after configurable TTL (e.g., 5 minutes) to avoid stale captures.
- Clarification prompts:
  - Missing purpose: “I saw an amount of {X}. What is this for?”
  - Low confidence: “I’m not sure about this expense. Please rephrase with amount + purpose.”
- Confirmation message:
  - “Logged: {amount} {currency} - {purpose}. Saved to row {N}.”
  - Include link to sheet (if `BALANCE_SHEET_ID` is configured) for quick verification.

## Group-to-Sheet Routing Strategy
- Default: all groups write to the main balance sheet (`BALANCE_SHEET_ID`) → `Ledger`.
- Optional mapping for future: env-driven JSON map `BALANCE_SHEET_BY_CHAT` to support multiple businesses (e.g., music school vs office); not required for first cut but design interfaces to accept `sheet_id` override by chat_id.

## Error Handling & Guardrails
- Ignore bot/command messages, stickers, media-only messages.
- Validation before append: must have amount_value > 0 and purpose length > 2.
- Rate-limit writes per user (e.g., max 5/min) to prevent spam.
- Catch Google Sheets errors and reply with actionable message; keep local log (stderr) for ops.
- If MCP unavailable, fall back to simple regex parser and ask user to confirm.

## Components To Add/Change
- New MCP client wrapper: `src/infrastructure/llm/expense_parser_client.py`.
- Extend `GoogleSheetsService` with append helpers and worksheet bootstrap.
- Extend `BalanceSummaryHandler` to:
  - Own parsing + follow-up logic.
  - Accept injected `ExpenseParserClient` and `GoogleSheetsService`.
  - Provide hooks for chat-level sheet routing.
- Update `BalanceBotApplication` to register the group MessageHandler and wire dependencies.

## Open Questions / Assumptions
- Sheet structure: assuming we can add a new `Ledger` worksheet; confirm no permission issues.
- Currency defaults: assume USD if message uses `$` and KHR if `៛/riel`; otherwise keep `UNKNOWN`.
- Do we need approval before write? For now, immediate write after parse/confirmation; can add admin-only mode later.
- Multi-amount messages: we will capture the first obvious expense unless user clarifies.

## Next Steps
1) Confirm target worksheet name and any existing ledger columns.
2) Define MCP endpoint/config and confidence thresholds (e.g., <0.6 → ask again).
3) Implement MCP client, Sheet append, and handler flow with tests for parsing/append logic.
