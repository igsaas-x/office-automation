from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime
from ...application.use_cases.record_trip import RecordTripUseCase
from ...application.use_cases.record_fuel import RecordFuelUseCase
from ...application.dto.trip_dto import RecordTripRequest
from ...application.dto.fuel_dto import RecordFuelRequest
from ...domain.repositories.vehicle_repository import IVehicleRepository
from ...infrastructure.utils.datetime_utils import format_time_ict

# Conversation states
SELECT_VEHICLE_FOR_TRIP = 30
ENTER_TRIP_COUNT = 31
ENTER_TOTAL_LOADING_SIZE = 32
SELECT_VEHICLE_FOR_FUEL = 40
ENTER_FUEL_LITERS = 41
ENTER_FUEL_COST = 42
UPLOAD_FUEL_RECEIPT = 43

class VehicleOperationsHandler:
    def __init__(
        self,
        record_trip_use_case: RecordTripUseCase,
        record_fuel_use_case: RecordFuelUseCase,
        vehicle_repository: IVehicleRepository
    ):
        self.record_trip_use_case = record_trip_use_case
        self.record_fuel_use_case = record_fuel_use_case
        self.vehicle_repository = vehicle_repository

    # ==================== Trip Recording ====================

    async def start_trip_recording(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start trip recording flow"""
        query = update.callback_query
        if query:
            await query.answer()

        chat = update.effective_chat
        context.user_data['operation_group_id'] = chat.id

        # Get group from database
        from ...infrastructure.persistence.database import database
        from ...infrastructure.persistence.group_repository_impl import GroupRepository

        session = database.get_session()
        group_repo = GroupRepository(session)
        group = group_repo.find_by_chat_id(str(chat.id))

        if not group:
            message = "❌ កំហុស: រកមិនឃើញក្រុម។ សូមចុះឈ្មោះជាមុនសិន។"
            if query:
                await query.edit_message_text(message)
            else:
                await update.message.reply_text(message)
            session.close()
            return ConversationHandler.END

        # Get all vehicles
        vehicles = self.vehicle_repository.find_by_group_id(group.id)
        session.close()

        if not vehicles:
            message = (
                "⚠️ រកមិនឃើញឡានទេ!\n\n"
                "សូមរៀបចំឡានជាមុនសិនដោយប្រើ /setup"
            )
            if query:
                await query.edit_message_text(message)
            else:
                await update.message.reply_text(message)
            return ConversationHandler.END

        # Show vehicle selection
        keyboard = []
        type_emoji = {"TRUCK": "🚚", "VAN": "🚐", "MOTORCYCLE": "🏍️", "CAR": "🚗"}
        for vehicle in vehicles:
            emoji = type_emoji.get(vehicle.vehicle_type, "🚗")

            # Show vehicle with driver name if available
            label = f"{emoji} {vehicle.license_plate}"
            if vehicle.driver_name:
                label += f" ({vehicle.driver_name})"

            keyboard.append([
                InlineKeyboardButton(label, callback_data=f"trip_vehicle_{vehicle.id}")
            ])

        keyboard.append([InlineKeyboardButton("🔙 ត្រឡប់", callback_data="menu_daily_operation")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        message_text = "🚚 កត់ត្រាចំនួនដឹក\n\nជ្រើសរើសឡាន:"

        if query:
            await query.edit_message_text(message_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message_text, reply_markup=reply_markup)

        return SELECT_VEHICLE_FOR_TRIP

    async def select_trip_vehicle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Vehicle selected, ask for trip count"""
        query = update.callback_query
        await query.answer()

        vehicle_id = int(query.data.replace("trip_vehicle_", ""))
        context.user_data['trip_vehicle_id'] = vehicle_id

        # Get vehicle info
        vehicle = self.vehicle_repository.find_by_id(vehicle_id)
        if not vehicle:
            await query.edit_message_text("❌ កំហុស: រកមិនឃើញឡាន។")
            return ConversationHandler.END

        context.user_data['trip_vehicle_plate'] = vehicle.license_plate

        await query.edit_message_text(
            f"🚚 កត់ត្រាចំនួនដឹកសម្រាប់ {vehicle.license_plate}\n\n"
            "សូមបញ្ចូលចំនួនដឹកសរុបសម្រាប់ថ្ងៃនេះ:\n"
            "ឧទាហរណ៍: 5"
        )

        return ENTER_TRIP_COUNT

    async def receive_trip_count(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive trip count and ask for total loading size"""
        try:
            trip_count = int(update.message.text.strip())
            if trip_count <= 0:
                raise ValueError("ចំនួនដឹកត្រូវតែធំជាង 0")

            context.user_data['trip_count'] = trip_count
            vehicle_plate = context.user_data.get('trip_vehicle_plate')

            await update.message.reply_text(
                f"ចំនួនដឹក: {trip_count} ជើង\n\n"
                "សូមបញ្ចូលទំហំផ្ទុកសរុបសម្រាប់ការដឹកទាំងអស់គិតជាម៉ែត្រគូប (m³):\n"
                "ឧទាហរណ៍: 25 ឬ 25.5"
            )

            return ENTER_TOTAL_LOADING_SIZE

        except ValueError as e:
            await update.message.reply_text(
                f"❌ ព័ត៌មានមិនត្រឹមត្រូវ: {str(e)}\n\n"
                "សូមបញ្ចូលលេខត្រឹមត្រូវសម្រាប់ចំនួនដឹក:"
            )
            return ENTER_TRIP_COUNT

    async def receive_total_loading_size(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive total loading size and create multiple trips"""
        try:
            total_loading_size = float(update.message.text.strip())
            if total_loading_size <= 0:
                raise ValueError("ទំហំផ្ទុកសរុបត្រូវតែធំជាង 0")

            context.user_data['total_loading_size'] = total_loading_size

        except ValueError as e:
            await update.message.reply_text(
                f"❌ ព័ត៌មានមិនត្រឹមត្រូវ: {str(e)}\n\n"
                "សូមបញ្ចូលលេខត្រឹមត្រូវសម្រាប់ទំហំផ្ទុកសរុប (គិតជាម៉ែត្រគូប):"
            )
            return ENTER_TOTAL_LOADING_SIZE

        # Get stored data
        vehicle_id = context.user_data.get('trip_vehicle_id')
        vehicle_plate = context.user_data.get('trip_vehicle_plate')
        trip_count = context.user_data.get('trip_count')

        # Calculate loading size per trip (distributed equally)
        loading_size_per_trip = total_loading_size / trip_count

        # Get group from database
        from ...infrastructure.persistence.database import database
        from ...infrastructure.persistence.group_repository_impl import GroupRepository

        session = database.get_session()
        group_repo = GroupRepository(session)
        group = group_repo.find_by_chat_id(str(context.user_data['operation_group_id']))

        if not group:
            await update.message.reply_text("❌ កំហុស: រកមិនឃើញក្រុម។")
            session.close()
            return ConversationHandler.END

        # Get vehicle
        vehicle = self.vehicle_repository.find_by_id(vehicle_id)
        if not vehicle:
            await update.message.reply_text("❌ កំហុស: រកមិនឃើញឡាន។")
            session.close()
            return ConversationHandler.END

        try:
            # Create multiple trips
            created_trips = []
            for i in range(trip_count):
                request = RecordTripRequest(
                    group_id=group.id,
                    vehicle_id=vehicle_id,
                    loading_size_cubic_meters=loading_size_per_trip
                )
                response = self.record_trip_use_case.execute(request)
                created_trips.append(response)

            # Get total trips today
            from datetime import date
            from ...infrastructure.persistence.trip_repository_impl import TripRepository
            trip_repo = TripRepository(session)
            total_today = trip_repo.count_by_vehicle_and_date(vehicle_id, date.today())

            type_emoji = {"TRUCK": "🚚", "VAN": "🚐", "MOTORCYCLE": "🏍️", "CAR": "🚗"}
            emoji = type_emoji.get(vehicle.vehicle_type, "🚗")

            # Get the last created trip for display
            last_trip = created_trips[-1]
            first_trip_num = created_trips[0].trip_number
            last_trip_num = last_trip.trip_number

            message_parts = [
                f"✅ {trip_count} បានកត់ត្រាសម្រាប់ឡាន: {last_trip.vehicle_license_plate}\n",
                # f"ឡាន: {emoji} {last_trip.vehicle_license_plate}"
            ]

            if last_trip.driver_name:
                message_parts.append(f"អ្នកបើកបរ: {last_trip.driver_name}")

            message_parts.extend([
                # f"លេខដំណើរ: #{first_trip_num} - #{last_trip_num}",
                f"ចំនួនជើងសរុប: {trip_count}",
                f"ទំហំផ្ទុកសរុប: {total_loading_size}m³",
                f"កាលបរិច្ឆេទ: {last_trip.date}",
                # f"ពេលវេលា: {format_time_ict(datetime.fromisoformat(last_trip.created_at))}\n",
                # f"ដំណើរសរុបថ្ងៃនេះ: {total_today}"
            ])

            await update.message.reply_text("\n".join(message_parts))

        except Exception as e:
            await update.message.reply_text(f"❌ កំហុស: {str(e)}")
        finally:
            session.close()

        return ConversationHandler.END

    # ==================== Fuel Recording ====================

    async def start_fuel_recording(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start fuel recording flow"""
        query = update.callback_query
        if query:
            await query.answer()

        chat = update.effective_chat
        context.user_data['operation_group_id'] = chat.id

        # Get group from database
        from ...infrastructure.persistence.database import database
        from ...infrastructure.persistence.group_repository_impl import GroupRepository

        session = database.get_session()
        group_repo = GroupRepository(session)
        group = group_repo.find_by_chat_id(str(chat.id))

        if not group:
            message = "❌ កំហុស: រកមិនឃើញក្រុម។"
            if query:
                await query.edit_message_text(message)
            else:
                await update.message.reply_text(message)
            session.close()
            return ConversationHandler.END

        # Get all vehicles
        vehicles = self.vehicle_repository.find_by_group_id(group.id)
        session.close()

        if not vehicles:
            message = "⚠️ រកមិនឃើញឡានទេ!\n\nសូមរៀបចំឡានជាមុនសិនដោយប្រើ /setup"
            if query:
                await query.edit_message_text(message)
            else:
                await update.message.reply_text(message)
            return ConversationHandler.END

        # Show vehicle selection
        keyboard = []
        type_emoji = {"TRUCK": "🚚", "VAN": "🚐", "MOTORCYCLE": "🏍️", "CAR": "🚗"}
        for vehicle in vehicles:
            emoji = type_emoji.get(vehicle.vehicle_type, "🚗")
            keyboard.append([
                InlineKeyboardButton(
                    f"{emoji} {vehicle.license_plate}",
                    callback_data=f"fuel_vehicle_{vehicle.id}"
                )
            ])

        keyboard.append([InlineKeyboardButton("🔙 ត្រឡប់", callback_data="menu_daily_operation")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        message_text = "⛽ កត់ត្រាសាំង\n\nជ្រើសរើសឡាន:"

        if query:
            await query.edit_message_text(message_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message_text, reply_markup=reply_markup)

        return SELECT_VEHICLE_FOR_FUEL

    async def select_fuel_vehicle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Vehicle selected, ask for liters"""
        query = update.callback_query
        await query.answer()

        vehicle_id = int(query.data.replace("fuel_vehicle_", ""))
        context.user_data['fuel_vehicle_id'] = vehicle_id

        # Get vehicle info
        vehicle = self.vehicle_repository.find_by_id(vehicle_id)
        if not vehicle:
            await query.edit_message_text("❌ កំហុស: រកមិនឃើញឡាន។")
            return ConversationHandler.END

        context.user_data['fuel_vehicle_plate'] = vehicle.license_plate

        await query.edit_message_text(
            f"⛽ កត់ត្រាសាំងសម្រាប់ {vehicle.license_plate}\n\n"
            "សូមបញ្ចូលចំនួនលីត្រ:\n"
            "ឧទាហរណ៍: 50 ឬ 50.5"
        )

        return ENTER_FUEL_LITERS

    async def receive_fuel_liters(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive liters, ask for cost"""
        try:
            liters = float(update.message.text.strip())
            if liters <= 0:
                raise ValueError("ចំនួនលីត្រត្រូវតែធំជាង 0")

            context.user_data['fuel_liters'] = liters

            await update.message.reply_text(
                f"លីត្រ: {liters}L\n\n"
                "សូមបញ្ចូលថ្លៃ (ដុល្លារ):\n"
                "ឧទាហរណ៍: 50 ឬ 50.25"
            )

            return ENTER_FUEL_COST

        except ValueError as e:
            await update.message.reply_text(
                f"❌ ព័ត៌មានមិនត្រឹមត្រូវ: {str(e)}\n\n"
                "សូមបញ្ចូលលេខត្រឹមត្រូវសម្រាប់ចំនួនលីត្រ:"
            )
            return ENTER_FUEL_LITERS

    async def receive_fuel_cost(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive cost, ask for receipt photo (optional)"""
        try:
            cost = float(update.message.text.strip())
            if cost <= 0:
                raise ValueError("ថ្លៃត្រូវតែធំជាង 0")

            context.user_data['fuel_cost'] = cost

            keyboard = [[InlineKeyboardButton("⏭️ រំលង", callback_data="fuel_skip_photo")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"ថ្លៃ: ${cost:,.2f}\n\n"
                "ផ្ទុកឡើងរូបថតបង្កាន់ដៃ (អាចរំលងបាន):\n"
                "ផ្ញើរូបថត ឬចុចរំលង",
                reply_markup=reply_markup
            )

            return UPLOAD_FUEL_RECEIPT

        except ValueError as e:
            await update.message.reply_text(
                f"❌ ព័ត៌មានមិនត្រឹមត្រូវ: {str(e)}\n\n"
                "សូមបញ្ចូលលេខត្រឹមត្រូវសម្រាប់ថ្លៃ:"
            )
            return ENTER_FUEL_COST

    async def complete_fuel_record(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Complete fuel recording (with or without photo)"""
        receipt_url = None

        # Check if photo was uploaded
        if update.message and update.message.photo:
            # TODO: Implement photo storage service
            # For now, we'll just note that a photo was received
            receipt_url = "photo_placeholder"
            message = update.message
        else:
            # Skip button pressed
            query = update.callback_query
            await query.answer()
            message = query.message

        # Get stored data
        vehicle_id = context.user_data.get('fuel_vehicle_id')
        vehicle_plate = context.user_data.get('fuel_vehicle_plate')
        liters = context.user_data.get('fuel_liters')
        cost = context.user_data.get('fuel_cost')

        # Get group from database
        from ...infrastructure.persistence.database import database
        from ...infrastructure.persistence.group_repository_impl import GroupRepository

        session = database.get_session()
        group_repo = GroupRepository(session)
        group = group_repo.find_by_chat_id(str(context.user_data['operation_group_id']))

        if not group:
            await message.reply_text("❌ កំហុស: រកមិនឃើញក្រុម។")
            session.close()
            return ConversationHandler.END

        try:
            # Record fuel
            request = RecordFuelRequest(
                group_id=group.id,
                vehicle_id=vehicle_id,
                liters=liters,
                cost=cost,
                receipt_photo_url=receipt_url
            )
            response = self.record_fuel_use_case.execute(request)

            receipt_status = "✅ បានរក្សាទុក" if receipt_url else "គ្មានបង្កាន់ដៃ"

            await message.reply_text(
                f"⛽ សាំងត្រូវបានកត់ត្រាសម្រាប់ {vehicle_plate}\n\n"
                f"កាលបរិច្ឆេទ: {response.date}\n"
                f"លីត្រ: {response.liters}L\n"
                f"ថ្លៃ: ${response.cost:,.2f}\n"
                f"បង្កាន់ដៃ: {receipt_status}"
            )

        except Exception as e:
            await message.reply_text(f"❌ កំហុស: {str(e)}")
        finally:
            session.close()

        return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel operation"""
        await update.message.reply_text("ប្រតិបត្តិការត្រូវបានបោះបង់។")
        return ConversationHandler.END
