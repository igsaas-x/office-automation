from ...infrastructure.google_sheets.sheets_service import GoogleSheetsService

class GetBalanceSummaryUseCase:
    def __init__(self, sheets_service: GoogleSheetsService):
        self.sheets_service = sheets_service

    def execute(self) -> str:
        """
        Get the balance summary from Google Sheets
        Returns formatted balance summary string
        """
        return self.sheets_service.get_balance_summary()
