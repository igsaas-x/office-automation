import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta
from ..config.settings import settings

class GoogleSheetsService:
    LEDGER_HEADERS = ["No", "Date", "Item", "Amount (USD)", "Amount (KHR)"]
    DEFAULT_LEDGER_START_COL = 8  # Column H to match existing sheet layout

    def __init__(self):
        self.credentials_file = 'credentials.json'
        self.client = None

    def _authenticate(self):
        """Authenticate with Google Sheets API"""
        if self.client is None:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=scopes
            )
            self.client = gspread.authorize(creds)
        return self.client

    def _escape_html(self, text: str) -> str:
        """Escape special HTML characters for Telegram"""
        text = str(text)
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text

    def get_balance_summary(self, month: str = None, sheet_id: str = None, sheet_url: str = None) -> str:
        """
        Read balance data from Google Sheets and format it for display

        Args:
            month: Optional month name (e.g., "January", "February"). If None, uses current month.
            sheet_id: Optional Google Sheets ID. If None, uses settings.BALANCE_SHEET_ID.
            sheet_url: Optional full Google Sheets URL for the "View Full Details" link.

        Returns formatted balance summary as string
        """
        try:
            # Get current time in Cambodia timezone (UTC+7)
            cambodia_tz = timezone(timedelta(hours=7))
            current_time = datetime.now(cambodia_tz)

            # Generate sheet name from provided month or current month
            sheet_name = month if month else current_time.strftime("%B")  # Full month name with first capital
            formatted_date = current_time.strftime("%d/%m/%Y %I:%M %p")

            # Use provided sheet_id or fall back to settings
            target_sheet_id = sheet_id if sheet_id else settings.BALANCE_SHEET_ID

            client = self._authenticate()
            sheet = client.open_by_key(target_sheet_id)

            # Try to get the worksheet by month name
            try:
                worksheet = sheet.worksheet(sheet_name)
            except Exception:
                return f"❌ Summary for this month ({sheet_name}) does not exist."

            # Get specific range B38:C44 for the balance summary
            values = worksheet.get('B38:C44')

            if not values:
                return "No balance data found in the sheet."

            # Format the data for display with HTML table
            formatted_text = "📊 <b>Account Balance Summary</b>\n"
            formatted_text += f"<i>Report Month: {sheet_name}</i>\n"
            formatted_text += f"<i>Date: {formatted_date}</i>\n\n"

            # First row is the title, skip it and start from row 2 (headers)
            if len(values) > 1:
                # Calculate max width for proper alignment
                data_rows = values[1:]  # Skip title row
                max_item_length = max(len(str(row[0])) for row in data_rows if len(row) >= 2)

                # Create table with monospace formatting
                formatted_text += "<pre>"

                # Print header row
                if len(data_rows) > 0 and len(data_rows[0]) >= 2:
                    header_item = str(data_rows[0][0])
                    header_amount = str(data_rows[0][1])
                    padded_header = header_item.ljust(max_item_length + 2)
                    formatted_text += f"{padded_header} {header_amount}\n"

                    # Add separator line
                    separator = "-" * (max_item_length + 2 + len(header_amount) + 1)
                    formatted_text += f"{separator}\n"

                # Print data rows (skip the first row which is the header)
                for i, row in enumerate(data_rows[1:]):
                    if len(row) >= 2:
                        item = str(row[0])
                        amount = str(row[1])

                        # Pad the item to align amounts
                        padded_item = item.ljust(max_item_length + 2)
                        formatted_text += f"{padded_item} {amount}\n"

                formatted_text += "</pre>"

            # Add link to view full spreadsheet details
            default_url = "https://docs.google.com/spreadsheets/d/1ZiEstn6X-vcJ8AIMbikg7ObPBa85EdkCNEPxGiUgkMo/edit?usp=sharing"
            link_url = sheet_url if sheet_url else default_url
            formatted_text += f'\n\n📄 <a href="{link_url}">View Full Details</a>'

            return formatted_text

        except FileNotFoundError:
            return f"❌ Error: Credentials file '{self.credentials_file}' not found.\n\nPlease ensure you have:\n1. Created Google Sheets API credentials\n2. Downloaded the credentials.json file\n3. Placed it in the project root\n4. Updated your .env file"
        except Exception as e:
            error_msg = str(e)
            # Don't use markdown in error messages to avoid parsing issues
            return f"Error reading balance summary: {error_msg}"

    # New helpers for expense ledger appends
    def append_expense_record(
        self,
        item: str,
        amount: float,
        currency: str,
        sheet_id: str = None,
        occurred_at: datetime = None
    ) -> dict:
        """
        Append a single expense row into the current month sheet.

        Returns a dict with sheet metadata (worksheet title, row number).
        """
        if amount is None or amount <= 0:
            raise ValueError("Amount must be greater than zero")

        local_time = occurred_at or datetime.now(timezone(timedelta(hours=7)))
        sheet_title = local_time.strftime("%B")  # e.g., December
        date_display = local_time.strftime("%b %d")  # e.g., Dec 03

        target_sheet_id = sheet_id if sheet_id else settings.BALANCE_SHEET_ID
        client = self._authenticate()
        sheet = client.open_by_key(target_sheet_id)

        worksheet = self._get_or_create_month_sheet(sheet, sheet_title)
        header_row, start_col = self._ensure_headers(worksheet)

        next_row = self._next_row_number(worksheet, start_col, header_row)
        row_index = next_row  # includes header row counting
        next_no = self._next_sequence_number(worksheet, start_col, header_row)

        usd_value = amount if currency.upper() == "USD" or currency.upper() == "UNKNOWN" else ""
        khr_value = amount if currency.upper() == "KHR" else ""

        values = [[next_no, date_display, item, usd_value, khr_value]]
        start_letter = self._col_to_letter(start_col)
        end_letter = self._col_to_letter(start_col + len(values[0]) - 1)
        range_ref = f"{start_letter}{row_index}:{end_letter}{row_index}"
        worksheet.update(range_ref, values, value_input_option="USER_ENTERED")

        return {"worksheet": sheet_title, "row": row_index, "sequence": next_no}

    def _get_or_create_month_sheet(self, sheet, sheet_title: str):
        try:
            return sheet.worksheet(sheet_title)
        except Exception:
            # Create with enough rows/cols for typical usage
            return sheet.add_worksheet(title=sheet_title, rows="500", cols="10")

    def _ensure_headers(self, worksheet):
        """
        Ensure ledger headers exist.
        Returns (header_row_index, start_col_index).
        """
        found = self._find_header_position(worksheet)
        if found:
            return found

        start_col = self.DEFAULT_LEDGER_START_COL
        header_row = 1
        start_letter = self._col_to_letter(start_col)
        end_letter = self._col_to_letter(start_col + len(self.LEDGER_HEADERS) - 1)
        worksheet.update(f"{start_letter}{header_row}:{end_letter}{header_row}", [self.LEDGER_HEADERS])
        return header_row, start_col

    def _find_header_position(self, worksheet):
        """Search the first few rows for the header sequence."""
        try:
            grid = worksheet.get("A1:Z5")
        except Exception:
            return None

        for row_idx, row in enumerate(grid, start=1):
            for col_idx in range(0, len(row) - len(self.LEDGER_HEADERS) + 1):
                segment = row[col_idx:col_idx + len(self.LEDGER_HEADERS)]
                if segment == self.LEDGER_HEADERS:
                    return row_idx, col_idx + 1  # 1-based column index
        return None

    def _next_row_number(self, worksheet, start_col: int, header_row: int) -> int:
        """Return the next row index (1-based) after the last non-empty row for the target columns."""
        all_values = worksheet.get_all_values()
        end_col = start_col + len(self.LEDGER_HEADERS) - 1
        last_row_with_data = header_row

        for idx, row in enumerate(all_values, start=1):
            if idx < header_row:
                continue
            extended = row + [""] * (end_col - len(row) + 1)
            if any(cell.strip() for cell in extended[start_col - 1:end_col]):
                last_row_with_data = idx

        return last_row_with_data + 1

    def _next_sequence_number(self, worksheet, start_col: int, header_row: int) -> int:
        """Return next sequence for 'No' column (ignoring header)."""
        all_values = worksheet.get_all_values()
        numeric_values = []
        for idx, row in enumerate(all_values, start=1):
            if idx <= header_row:
                continue
            if len(row) < start_col:
                continue
            value = row[start_col - 1]
            try:
                numeric_values.append(int(value))
            except (TypeError, ValueError):
                continue
        if not numeric_values:
            return 1
        return max(numeric_values) + 1

    def _col_to_letter(self, col: int) -> str:
        """Convert 1-based column index to letter (1=A)."""
        result = ""
        while col > 0:
            col, remainder = divmod(col - 1, 26)
            result = chr(65 + remainder) + result
        return result
