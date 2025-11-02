from ...infrastructure.google_sheets.sheets_service import GoogleSheetsService

class GetBalanceSummaryUseCase:
    def __init__(self, sheets_service: GoogleSheetsService):
        self.sheets_service = sheets_service

    def execute(self, month: str = None, sheet_id: str = None, sheet_url: str = None) -> str:
        """
        Get the balance summary from Google Sheets

        Args:
            month: Optional month name (e.g., "January", "February"). If None, uses current month.
            sheet_id: Optional Google Sheets ID. If None, uses settings.BALANCE_SHEET_ID.
            sheet_url: Optional full Google Sheets URL for the "View Full Details" link.

        Returns formatted balance summary string
        """
        return self.sheets_service.get_balance_summary(month, sheet_id, sheet_url)
