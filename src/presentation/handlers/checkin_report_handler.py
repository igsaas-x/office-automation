"""
Check-in Report Handler
Shows daily and monthly employee check-in reports in Telegram
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, date, timedelta
from typing import List
from ...domain.repositories.group_repository import IGroupRepository
from ...domain.repositories.check_in_repository import ICheckInRepository
from ...domain.repositories.employee_repository import IEmployeeRepository


class CheckInReportHandler:
    """Handler for showing check-in reports in Telegram"""

    def __init__(
        self,
        group_repository: IGroupRepository,
        check_in_repository: ICheckInRepository,
        employee_repository: IEmployeeRepository
    ):
        self.group_repository = group_repository
        self.check_in_repository = check_in_repository
        self.employee_repository = employee_repository

    async def show_report_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show report type selection menu"""
        chat = update.effective_chat
        message = update.effective_message

        # Only works in group chats
        if chat.type not in ['group', 'supergroup']:
            await message.reply_text(
                "⚠️ ពាក្យបញ្ជានេះដំណើរការតែនៅក្នុងការសន្ទនាក្រុមប៉ុណ្ណោះ។\n\n"
                "This command only works in group chats."
            )
            return

        # Check if group is registered
        group = self.group_repository.find_by_chat_id(str(chat.id))
        if not group:
            await message.reply_text(
                "⚠️ ក្រុមនេះមិនទាន់ចុះឈ្មោះទេ។\n"
                "សូមសួរអ្នកគ្រប់គ្រង ឱ្យរត់ពាក្យបញ្ជា /register ជាមុនសិន។\n\n"
                "This group is not registered.\n"
                "Please ask an admin to run /register first."
            )
            return

        # Show report type selection
        keyboard = [
            [InlineKeyboardButton("📅 របាយការណ៍ថ្ងៃនេះ Today's Report", callback_data=f"report_daily_{group.id}")],
            [InlineKeyboardButton("📆 របាយការណ៍ខែនេះ Monthly Report", callback_data=f"report_monthly_{group.id}")],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await message.reply_text(
            f"**{group.business_name or group.name}**\n\n"
            f"📊 **របាយការណ៍ការចុះឈ្មោះ Check-In Reports**\n\n"
            f"សូមជ្រើសរើសប្រភេទរបាយការណ៍:\n"
            f"Please select report type:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def show_daily_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE, group_id: int):
        """Show today's check-in report"""
        query = update.callback_query
        await query.answer()

        # Get group
        group = self.group_repository.find_by_id(group_id)
        if not group:
            await query.edit_message_text("⚠️ Group not found.")
            return

        # Get today's check-ins
        today = date.today()
        check_ins = self.check_in_repository.find_by_group_and_date(group_id, today)

        # Format report
        report_text = self._format_daily_report(group, check_ins, today)

        await query.edit_message_text(report_text, parse_mode='Markdown')

    async def show_monthly_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE, group_id: int):
        """Show this month's check-in report"""
        query = update.callback_query
        await query.answer()

        # Get group
        group = self.group_repository.find_by_id(group_id)
        if not group:
            await query.edit_message_text("⚠️ Group not found.")
            return

        # Get this month's check-ins
        today = date.today()
        start_of_month = today.replace(day=1)
        check_ins = self.check_in_repository.find_by_group_and_date_range(
            group_id,
            start_of_month,
            today
        )

        # Format report
        report_text = self._format_monthly_report(group, check_ins, today)

        await query.edit_message_text(report_text, parse_mode='Markdown')

    def _format_daily_report(self, group, check_ins, report_date) -> str:
        """Format daily check-in report"""
        business_name = group.business_name or group.name
        date_str = report_date.strftime("%d/%m/%Y")

        if not check_ins:
            return (
                f"**{business_name}**\n\n"
                f"📅 **របាយការណ៍ថ្ងៃនេះ Daily Report**\n"
                f"📆 **កាលបរិច្ឆេទ Date:** {date_str}\n\n"
                f"មិនមានការចុះឈ្មោះសម្រាប់ថ្ងៃនេះទេ។\n"
                f"No check-ins for today."
            )

        # Group check-ins by employee
        employee_checkins = {}
        for checkin in check_ins:
            emp_id = checkin.employee_id
            if emp_id not in employee_checkins:
                employee = self.employee_repository.find_by_id(emp_id)
                employee_checkins[emp_id] = {
                    'name': employee.name if employee else 'Unknown',
                    'checkins': []
                }
            employee_checkins[emp_id]['checkins'].append(checkin)

        # Format report
        report_lines = [
            f"**{business_name}**\n",
            f"📅 **របាយការណ៍ថ្ងៃនេះ Daily Report**",
            f"📆 **កាលបរិច្ឆេទ Date:** {date_str}",
            f"👥 **បុគ្គលិក Employees:** {len(employee_checkins)}",
            f"✅ **ចំនួនចុះឈ្មោះ Total Check-ins:** {len(check_ins)}\n",
            "---\n"
        ]

        # Add each employee's check-ins
        for emp_id, data in sorted(employee_checkins.items(), key=lambda x: x[1]['name']):
            report_lines.append(f"👤 **{data['name']}**")

            for idx, checkin in enumerate(data['checkins'], 1):
                time_str = checkin.timestamp.strftime("%H:%M:%S") if checkin.timestamp else "N/A"
                location = f"{checkin.latitude:.4f}, {checkin.longitude:.4f}" if checkin.latitude and checkin.longitude else "N/A"

                if len(data['checkins']) > 1:
                    report_lines.append(f"  • Check-in #{idx}: {time_str}")
                else:
                    report_lines.append(f"  🕒 {time_str}")
                report_lines.append(f"  📍 {location}")

            report_lines.append("")  # Empty line between employees

        return "\n".join(report_lines)

    def _format_monthly_report(self, group, check_ins, report_date) -> str:
        """Format monthly check-in report"""
        business_name = group.business_name or group.name
        month_year = report_date.strftime("%B %Y")

        if not check_ins:
            return (
                f"**{business_name}**\n\n"
                f"📆 **របាយការណ៍ខែនេះ Monthly Report**\n"
                f"📅 **ខែ Month:** {month_year}\n\n"
                f"មិនមានការចុះឈ្មោះសម្រាប់ខែនេះទេ។\n"
                f"No check-ins for this month."
            )

        # Group check-ins by employee
        employee_stats = {}
        for checkin in check_ins:
            emp_id = checkin.employee_id
            if emp_id not in employee_stats:
                employee = self.employee_repository.find_by_id(emp_id)
                employee_stats[emp_id] = {
                    'name': employee.name if employee else 'Unknown',
                    'count': 0,
                    'dates': set()
                }
            employee_stats[emp_id]['count'] += 1
            if checkin.timestamp:
                employee_stats[emp_id]['dates'].add(checkin.timestamp.date())

        # Format report
        report_lines = [
            f"**{business_name}**\n",
            f"📆 **របាយការណ៍ខែនេះ Monthly Report**",
            f"📅 **ខែ Month:** {month_year}",
            f"👥 **បុគ្គលិក Employees:** {len(employee_stats)}",
            f"✅ **ចំនួនចុះឈ្មោះសរុប Total Check-ins:** {len(check_ins)}\n",
            "---\n"
        ]

        # Add each employee's stats
        for emp_id, data in sorted(employee_stats.items(), key=lambda x: x[1]['count'], reverse=True):
            unique_days = len(data['dates'])
            report_lines.append(
                f"👤 **{data['name']}**\n"
                f"  ✅ {data['count']} check-ins\n"
                f"  📅 {unique_days} days\n"
            )

        return "\n".join(report_lines)
