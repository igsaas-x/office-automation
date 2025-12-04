from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime
from ...application.use_cases.record_trip import RecordTripUseCase
from ...application.use_cases.record_fuel import RecordFuelUseCase
from ...application.dto.trip_dto import RecordTripRequest
from ...application.dto.fuel_dto import RecordFuelRequest
from ...domain.repositories.vehicle_repository import IVehicleRepository
from ...domain.repositories.driver_repository import IDriverRepository

# Conversation states
SELECT_VEHICLE_FOR_TRIP = 30
SELECT_VEHICLE_FOR_FUEL = 40
ENTER_FUEL_LITERS = 41
ENTER_FUEL_COST = 42
UPLOAD_FUEL_RECEIPT = 43

class VehicleOperationsHandler:
    def __init__(
        self,
        record_trip_use_case: RecordTripUseCase,
        record_fuel_use_case: RecordFuelUseCase,
        vehicle_repository: IVehicleRepository,
        driver_repository: IDriverRepository
    ):
        self.record_trip_use_case = record_trip_use_case
        self.record_fuel_use_case = record_fuel_use_case
        self.vehicle_repository = vehicle_repository
        self.driver_repository = driver_repository

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
            message = "❌ Error: Group not found. Please register first."
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
                "⚠️ No vehicles found!\n\n"
                "Please setup a vehicle first using /setup"
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
            # Get driver name
            drivers = self.driver_repository.find_by_group_id(group.id)
            driver_name = None
            for driver in drivers:
                if driver.assigned_vehicle_id == vehicle.id:
                    driver_name = driver.name
                    break

            label = f"{emoji} {vehicle.license_plate}"
            if driver_name:
                label += f" ({driver_name})"

            keyboard.append([
                InlineKeyboardButton(label, callback_data=f"trip_vehicle_{vehicle.id}")
            ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        message_text = "🚚 Record Trip\n\nSelect vehicle:"

        if query:
            await query.edit_message_text(message_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message_text, reply_markup=reply_markup)

        return SELECT_VEHICLE_FOR_TRIP

    async def record_trip(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Record trip for selected vehicle"""
        query = update.callback_query
        await query.answer()

        vehicle_id = int(query.data.replace("trip_vehicle_", ""))

        # Get group from database
        from ...infrastructure.persistence.database import database
        from ...infrastructure.persistence.group_repository_impl import GroupRepository

        session = database.get_session()
        group_repo = GroupRepository(session)
        group = group_repo.find_by_chat_id(str(context.user_data['operation_group_id']))

        if not group:
            await query.edit_message_text("❌ Error: Group not found.")
            session.close()
            return ConversationHandler.END

        # Get vehicle and driver
        vehicle = self.vehicle_repository.find_by_id(vehicle_id)
        if not vehicle:
            await query.edit_message_text("❌ Error: Vehicle not found.")
            session.close()
            return ConversationHandler.END

        # Find driver assigned to this vehicle
        drivers = self.driver_repository.find_by_group_id(group.id)
        driver = None
        for d in drivers:
            if d.assigned_vehicle_id == vehicle_id:
                driver = d
                break

        if not driver:
            await query.edit_message_text(
                f"❌ Error: No driver assigned to {vehicle.license_plate}.\n\n"
                "Please assign a driver using /setup"
            )
            session.close()
            return ConversationHandler.END

        try:
            # Record trip
            request = RecordTripRequest(
                group_id=group.id,
                vehicle_id=vehicle_id,
                driver_id=driver.id
            )
            response = self.record_trip_use_case.execute(request)

            # Get total trips today
            from datetime import date
            from ...infrastructure.persistence.trip_repository_impl import TripRepository
            trip_repo = TripRepository(session)
            total_today = trip_repo.count_by_vehicle_and_date(vehicle_id, date.today())

            type_emoji = {"TRUCK": "🚚", "VAN": "🚐", "MOTORCYCLE": "🏍️", "CAR": "🚗"}
            emoji = type_emoji.get(vehicle.vehicle_type, "🚗")

            await query.edit_message_text(
                f"✅ Trip #{response.trip_number} recorded for {response.vehicle_license_plate}\n\n"
                f"Vehicle: {emoji} {response.vehicle_license_plate}\n"
                f"Driver: {response.driver_name}\n"
                f"Date: {response.date}\n"
                f"Time: {datetime.fromisoformat(response.created_at).strftime('%H:%M')}\n\n"
                f"Total trips today: {total_today}"
            )

        except Exception as e:
            await query.edit_message_text(f"❌ Error: {str(e)}")
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
            message = "❌ Error: Group not found."
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
            message = "⚠️ No vehicles found!\n\nPlease setup a vehicle first using /setup"
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

        reply_markup = InlineKeyboardMarkup(keyboard)
        message_text = "⛽ Record Fuel\n\nSelect vehicle:"

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
            await query.edit_message_text("❌ Error: Vehicle not found.")
            return ConversationHandler.END

        context.user_data['fuel_vehicle_plate'] = vehicle.license_plate

        await query.edit_message_text(
            f"⛽ Fuel Record for {vehicle.license_plate}\n\n"
            "Please enter the number of liters:\n"
            "Example: 50 or 50.5"
        )

        return ENTER_FUEL_LITERS

    async def receive_fuel_liters(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive liters, ask for cost"""
        try:
            liters = float(update.message.text.strip())
            if liters <= 0:
                raise ValueError("Liters must be greater than 0")

            context.user_data['fuel_liters'] = liters

            await update.message.reply_text(
                f"Liters: {liters}L\n\n"
                "Please enter the cost (រៀល/Dollar):\n"
                "Example: 250000 or 250000.50"
            )

            return ENTER_FUEL_COST

        except ValueError as e:
            await update.message.reply_text(
                f"❌ Invalid input: {str(e)}\n\n"
                "Please enter a valid number for liters:"
            )
            return ENTER_FUEL_LITERS

    async def receive_fuel_cost(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive cost, ask for receipt photo (optional)"""
        try:
            cost = float(update.message.text.strip())
            if cost <= 0:
                raise ValueError("Cost must be greater than 0")

            context.user_data['fuel_cost'] = cost

            keyboard = [[InlineKeyboardButton("⏭️ Skip", callback_data="fuel_skip_photo")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"Cost: {cost:,.0f} រៀល\n\n"
                "Upload receipt photo (optional):\n"
                "Send a photo or click Skip",
                reply_markup=reply_markup
            )

            return UPLOAD_FUEL_RECEIPT

        except ValueError as e:
            await update.message.reply_text(
                f"❌ Invalid input: {str(e)}\n\n"
                "Please enter a valid number for cost:"
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
            await message.reply_text("❌ Error: Group not found.")
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

            receipt_status = "✅ Uploaded" if receipt_url else "No receipt"

            await message.reply_text(
                f"⛽ Fuel recorded for {vehicle_plate}\n\n"
                f"Date: {response.date}\n"
                f"Liters: {response.liters}L\n"
                f"Cost: {response.cost:,.0f} រៀល\n"
                f"Receipt: {receipt_status}"
            )

        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
        finally:
            session.close()

        return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel operation"""
        await update.message.reply_text("Operation cancelled.")
        return ConversationHandler.END
