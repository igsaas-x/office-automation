import gspread
from google.oauth2.service_account import Credentials
from ..config.settings import settings

class GoogleSheetsService:
    def __init__(self):
        self.credentials_file = settings.GOOGLE_SHEETS_CREDENTIALS_FILE
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

    def get_balance_summary(self) -> str:
        """
        Read balance data from Google Sheets and format it for display
        Returns formatted balance summary as string
        """
        try:
            client = self._authenticate()
            sheet = client.open_by_key(settings.BALANCE_SHEET_ID)
            worksheet = sheet.worksheet(settings.BALANCE_SHEET_NAME)

            # Get all values from the sheet
            all_values = worksheet.get_all_values()

            if not all_values:
                return "No balance data found in the sheet."

            # Format the data for display
            formatted_text = "📊 *Organization Balance Summary*\n\n"

            # Assuming first row is headers
            headers = all_values[0]
            data_rows = all_values[1:]

            # Create a formatted table
            for row in data_rows:
                if row:  # Skip empty rows
                    row_text = " | ".join([f"{headers[i]}: {cell}" for i, cell in enumerate(row) if i < len(headers)])
                    formatted_text += f"{row_text}\n"

            return formatted_text

        except Exception as e:
            return f"Error reading balance summary: {str(e)}"
