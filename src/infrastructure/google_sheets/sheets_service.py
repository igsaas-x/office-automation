import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta
from ..config.settings import settings

class GoogleSheetsService:
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

    def get_balance_summary(self) -> str:
        """
        Read balance data from Google Sheets and format it for display
        Returns formatted balance summary as string
        """
        try:
            # Get current time in Cambodia timezone (UTC+7)
            cambodia_tz = timezone(timedelta(hours=7))
            current_time = datetime.now(cambodia_tz)

            # Generate sheet name from current month (e.g., "October")
            sheet_name = current_time.strftime("%B")  # Full month name with first capital
            formatted_date = current_time.strftime("%d/%m/%Y %I:%M %p")

            client = self._authenticate()
            sheet = client.open_by_key(settings.BALANCE_SHEET_ID)

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

            return formatted_text

        except FileNotFoundError:
            return f"❌ Error: Credentials file '{self.credentials_file}' not found.\n\nPlease ensure you have:\n1. Created Google Sheets API credentials\n2. Downloaded the credentials.json file\n3. Placed it in the project root\n4. Updated your .env file"
        except Exception as e:
            error_msg = str(e)
            # Don't use markdown in error messages to avoid parsing issues
            return f"Error reading balance summary: {error_msg}"
