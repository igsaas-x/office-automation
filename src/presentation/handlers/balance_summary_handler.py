import re
from datetime import datetime, timezone, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from ...application.use_cases.get_balance_summary import GetBalanceSummaryUseCase
from ...infrastructure.google_sheets.sheets_service import GoogleSheetsService
from ...infrastructure.llm.expense_parser_client import ExpenseParserClient, ParsedExpense

class BalanceSummaryHandler:
    # List of months for selection
    MONTHS = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    PENDING_TTL_SECONDS = 300

    def __init__(
        self,
        get_balance_summary_use_case: GetBalanceSummaryUseCase,
        sheets_service: GoogleSheetsService = None,
        expense_parser: ExpenseParserClient = None,
    ):
        self.get_balance_summary_use_case = get_balance_summary_use_case
        self.sheets_service = sheets_service
        self.expense_parser = expense_parser

    async def show_month_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                   callback_prefix: str = "BALANCE_MONTH", title: str = "📅 ជ្រើសរើសខែដើម្បីមើលសង្ខេបសមតុល្យ:"):
        """Show month selection keyboard

        Args:
            update: Telegram update
            context: Telegram context
            callback_prefix: Prefix for callback data (e.g., "BALANCE_MONTH" or "MUSIC_SCHOOL_MONTH")
            title: Message title to display
        """
        # Create inline keyboard with month buttons (3 columns)
        keyboard = []
        row = []
        for i, month in enumerate(self.MONTHS):
            row.append(InlineKeyboardButton(month, callback_data=f"{callback_prefix}_{month}"))
            if (i + 1) % 3 == 0:
                keyboard.append(row)
                row = []

        # Add any remaining buttons
        if row:
            keyboard.append(row)

        reply_markup = InlineKeyboardMarkup(keyboard)

        message = update.effective_message
        await message.reply_text(title, reply_markup=reply_markup)

    async def show_balance_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                   month: str = None, sheet_id: str = None, sheet_url: str = None):
        """Handle balance summary request for a specific month

        Args:
            update: Telegram update
            context: Telegram context
            month: Optional month name
            sheet_id: Optional Google Sheets ID
            sheet_url: Optional Google Sheets URL for the link
        """
        query = update.callback_query

        try:
            # Get balance summary for the specified month (or current if None)
            summary = self.get_balance_summary_use_case.execute(month, sheet_id, sheet_url)

            # If it's a callback query, edit the existing message
            if query:
                await query.answer()
                await query.edit_message_text(summary, parse_mode='HTML')
            else:
                # Otherwise, send a new message
                message = update.effective_message
                await message.reply_text(summary, parse_mode='HTML')
        except Exception as e:
            # If there's an error, send without formatting
            error_message = f"❌ បរាជ័យក្នុងការទាញយកសង្ខេបសមតុល្យ។\n\nកំហុស: {str(e)}"

            if query:
                await query.answer()
                await query.edit_message_text(error_message)
            else:
                message = update.effective_message
                await message.reply_text(error_message)

    async def handle_group_expense(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Listen to group text messages, parse amounts, and log to Sheets."""
        message = update.effective_message
        user = update.effective_user

        if not message or not user or user.is_bot:
            return

        text = message.text
        if not isinstance(text, str):
            return
        text = text.strip()
        if not text:
            return

        chat_data = context.chat_data
        pending_map = chat_data.setdefault("pending_expense", {})

        self._cleanup_pending(pending_map)
        pending_entry = pending_map.get(user.id)

        # If we are waiting for a purpose from this user, capture it even without numbers
        if pending_entry and not self._has_number(text):
            purpose_text = text.strip()
            if len(purpose_text) < 3:
                await message.reply_text("Please add a short purpose for the expense.")
                return
            await self._save_with_purpose(
                update,
                context,
                purpose=purpose_text,
                amount=pending_entry["amount"],
                currency=pending_entry["currency"],
                raw_text=pending_entry["raw_text"]
            )
            pending_map.pop(user.id, None)
            return

        if not self._has_number(text):
            return

        parsed = self.expense_parser.parse_message(text) if self.expense_parser else None
        if not parsed:
            amount_hint = self._extract_first_amount(text)
            hint_text = f" {self._format_amount(amount_hint, 'USD')}" if amount_hint else ""
            await message.reply_text(
                f"🤔 I saw a number{hint_text} but couldn't understand the expense. "
                "Please send amount + purpose (e.g., 25 coffee staff)."
            )
            return

        if not parsed.purpose or len(parsed.purpose) < 3:
            pending_map[user.id] = {
                "amount": parsed.amount_value,
                "currency": parsed.currency,
                "raw_text": text,
                "created_at": datetime.now(timezone.utc).timestamp()
            }
            await message.reply_text(
                f"👀 I saw an amount of {self._format_amount(parsed.amount_value, parsed.currency)}. "
                "What is this expense for?"
            )
            return

        if parsed.confidence < 0.6:
            await message.reply_text(
                f"🤔 I detected {self._format_amount(parsed.amount_value, parsed.currency)} "
                "but need a clearer purpose. Please resend with amount + purpose (e.g., 25 coffee staff)."
            )
            return

        await self._save_parsed_expense(update, context, parsed)

    def _cleanup_pending(self, pending_map: dict):
        """Drop stale pending prompts."""
        now_ts = datetime.now(timezone.utc).timestamp()
        stale_keys = [
            user_id for user_id, entry in pending_map.items()
            if now_ts - entry.get("created_at", 0) > self.PENDING_TTL_SECONDS
        ]
        for key in stale_keys:
            pending_map.pop(key, None)

    def _has_number(self, text: str) -> bool:
        cleaned = self._strip_usernames(text)
        return bool(re.search(r"[0-9\u17e0-\u17e9]", cleaned))

    def _extract_first_amount(self, text: str) -> float:
        """Best-effort amount extraction for user feedback."""
        normalized = self._normalize_digits(self._strip_usernames(text))
        match = re.search(r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?", normalized)
        if not match:
            return None
        try:
            return float(match.group(0).replace(",", ""))
        except ValueError:
            return None

    def _strip_usernames(self, text: str) -> str:
        """Remove telegram-style @usernames so digits inside handles are ignored."""
        return re.sub(r"@[A-Za-z0-9_]+", "", text or "")

    def _normalize_digits(self, text: str) -> str:
        khmer_digits = "០១២៣៤៥៦៧៨៩"
        ascii_digits = "0123456789"
        translation = str.maketrans(khmer_digits, ascii_digits)
        return (text or "").translate(translation)

    async def _save_with_purpose(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                 purpose: str, amount: float, currency: str, raw_text: str):
        parsed = ParsedExpense(
            amount_value=amount,
            currency=currency,
            purpose=purpose,
            confidence=0.7,
            raw_text=raw_text
        )
        await self._save_parsed_expense(update, context, parsed)

    async def _save_parsed_expense(self, update: Update, context: ContextTypes.DEFAULT_TYPE, parsed: ParsedExpense):
        if not self.sheets_service:
            await update.effective_message.reply_text("Sheets service not configured.")
            return

        message = update.effective_message
        try:
            append_result = self.sheets_service.append_expense_record(
                item=parsed.purpose,
                amount=parsed.amount_value,
                currency=parsed.currency,
            )
            await message.reply_text(
                f"✅ Noted #{append_result.get('sequence')}: "
                f"{self._format_amount(parsed.amount_value, parsed.currency)} - {parsed.purpose}"
            )
        except Exception as e:
            await message.reply_text(f"❌ Could not save expense: {str(e)}")

    def _format_amount(self, amount: float, currency: str) -> str:
        currency = (currency or "").upper()
        if currency == "KHR":
            return f"៛{self._format_number(amount)}"
        return f"${self._format_number(amount)}"

    def _format_number(self, amount: float) -> str:
        return f"{amount:,.2f}"
