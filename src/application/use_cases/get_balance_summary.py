from ...infrastructure.google_sheets.sheets_service import GoogleSheetsService

class GetBalanceSummaryUseCase:
    def __init__(self, sheets_service: GoogleSheetsService):
        self.sheets_service = sheets_service

    def execute(self, month: str = None) -> str:
        """
        Get the balance summary from Google Sheets

        Args:
            month: Optional month name (e.g., "January", "February"). If None, uses current month.

        Returns formatted balance summary string
        """
        return self.sheets_service.get_balance_summary(month)
