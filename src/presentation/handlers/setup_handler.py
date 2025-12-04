from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from ...application.use_cases.register_vehicle import RegisterVehicleUseCase
from ...application.use_cases.register_driver import RegisterDriverUseCase
from ...application.use_cases.register_group import RegisterGroupUseCase
from ...application.dto.vehicle_dto import RegisterVehicleRequest
from ...application.dto.driver_dto import RegisterDriverRequest
from ...domain.repositories.vehicle_repository import IVehicleRepository
from ...domain.repositories.driver_repository import IDriverRepository

# Conversation states
SETUP_MENU = 0
# Vehicle registration states
SETUP_VEHICLE_PLATE = 10
# Driver registration states
SETUP_DRIVER_NAME = 20
SETUP_DRIVER_ROLE = 21
SETUP_DRIVER_PHONE = 22
SETUP_DRIVER_VEHICLE = 23

class SetupHandler:
    def __init__(
        self,
        register_vehicle_use_case: RegisterVehicleUseCase,
        register_driver_use_case: RegisterDriverUseCase,
        register_group_use_case: RegisterGroupUseCase,
        vehicle_repository: IVehicleRepository,
        driver_repository: IDriverRepository
    ):
        self.register_vehicle_use_case = register_vehicle_use_case
        self.register_driver_use_case = register_driver_use_case
        self.register_group_use_case = register_group_use_case
        self.vehicle_repository = vehicle_repository
        self.driver_repository = driver_repository

    async def setup_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show setup menu with vehicle and driver options"""
        chat = update.effective_chat

        # Register group if not already registered
        try:
            self.register_group_use_case.execute(
                chat_id=str(chat.id),
                name=chat.title or f"Group {chat.id}"
            )
        except:
            pass  # Group already exists

        # Store group info
        context.user_data['setup_group_id'] = chat.id

        keyboard = [
            [InlineKeyboardButton("🚗 Setup Vehicle", callback_data="setup_vehicle")],
            [InlineKeyboardButton("👤 Setup Driver", callback_data="setup_driver")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message_text = (
            "⚙️ Setup Menu\n\n"
            "Choose what to setup:\n\n"
            "Note: Set up vehicles first, then drivers"
        )

        if update.callback_query:
            await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message_text, reply_markup=reply_markup)

        return SETUP_MENU

    # ==================== Vehicle Registration ====================

    async def start_vehicle_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start vehicle registration flow"""
        query = update.callback_query
        await query.answer()

        await query.edit_message_text(
            "🚗 Vehicle Setup\n\n"
            "Please enter the vehicle license plate (ស្លាកលេខឡាន):\n"
            "Example: PP-1234 or 2A-5678"
        )

        return SETUP_VEHICLE_PLATE

    async def receive_vehicle_plate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive vehicle license plate and save vehicle"""
        license_plate = update.message.text.strip()

        # Get group from database to get its ID
        from ...infrastructure.persistence.database import database
        from ...infrastructure.persistence.group_repository_impl import GroupRepository

        session = database.get_session()
        group_repo = GroupRepository(session)
        group = group_repo.find_by_chat_id(str(context.user_data['setup_group_id']))

        if not group:
            await update.message.reply_text("❌ Error: Group not found. Please try again.")
            session.close()
            return ConversationHandler.END

        try:
            # Register vehicle with default type "TRUCK"
            request = RegisterVehicleRequest(
                group_id=group.id,
                license_plate=license_plate,
                vehicle_type="TRUCK"  # Default type
            )
            response = self.register_vehicle_use_case.execute(request)

            # Show success message
            await update.message.reply_text(
                f"✅ Vehicle registered successfully!\n\n"
                f"License Plate: {response.license_plate}\n\n"
                "You can now setup drivers and assign them to this vehicle."
            )

        except ValueError as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
        finally:
            session.close()

        return ConversationHandler.END

    # ==================== Driver Registration ====================

    async def start_driver_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start driver registration flow"""
        query = update.callback_query
        await query.answer()

        await query.edit_message_text(
            "👤 Driver Setup\n\n"
            "Please enter the driver's name:"
        )

        return SETUP_DRIVER_NAME

    async def receive_driver_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive driver name"""
        driver_name = update.message.text.strip()
        context.user_data['driver_name'] = driver_name

        await update.message.reply_text(
            f"Name: {driver_name}\n\n"
            "Please enter the driver's role:\n"
            "Example: Driver, Manager, Supervisor"
        )

        return SETUP_DRIVER_ROLE

    async def receive_driver_role(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive driver role"""
        driver_role = update.message.text.strip()
        context.user_data['driver_role'] = driver_role

        await update.message.reply_text(
            f"Name: {context.user_data['driver_name']}\n"
            f"Role: {driver_role}\n\n"
            "Please enter the driver's phone number:\n"
            "Example: 012345678"
        )

        return SETUP_DRIVER_PHONE

    async def receive_driver_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive driver phone and show vehicle selection"""
        driver_phone = update.message.text.strip()
        context.user_data['driver_phone'] = driver_phone

        # Get group from database
        from ...infrastructure.persistence.database import database
        from ...infrastructure.persistence.group_repository_impl import GroupRepository

        session = database.get_session()
        group_repo = GroupRepository(session)
        group = group_repo.find_by_chat_id(str(context.user_data['setup_group_id']))

        if not group:
            await update.message.reply_text("❌ Error: Group not found.")
            session.close()
            return ConversationHandler.END

        # Get all vehicles for this group
        vehicles = self.vehicle_repository.find_by_group_id(group.id)
        session.close()

        if not vehicles:
            await update.message.reply_text(
                "⚠️ No vehicles found!\n\n"
                "Please setup a vehicle first using /setup → Setup Vehicle"
            )
            return ConversationHandler.END

        # Show vehicle selection
        keyboard = []
        type_emoji = {"TRUCK": "🚚", "VAN": "🚐", "MOTORCYCLE": "🏍️", "CAR": "🚗"}
        for vehicle in vehicles:
            emoji = type_emoji.get(vehicle.vehicle_type, "🚗")
            keyboard.append([
                InlineKeyboardButton(
                    f"{emoji} {vehicle.license_plate}",
                    callback_data=f"assign_vehicle_{vehicle.id}"
                )
            ])
        keyboard.append([InlineKeyboardButton("⏭️ Skip - Assign Later", callback_data="assign_vehicle_skip")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"Name: {context.user_data['driver_name']}\n"
            f"Phone: {driver_phone}\n\n"
            "Assign to vehicle:",
            reply_markup=reply_markup
        )

        return SETUP_DRIVER_VEHICLE

    async def receive_driver_vehicle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive vehicle assignment and save driver"""
        query = update.callback_query
        await query.answer()

        assigned_vehicle_id = None
        if query.data != "assign_vehicle_skip":
            assigned_vehicle_id = int(query.data.replace("assign_vehicle_", ""))

        driver_name = context.user_data.get('driver_name')
        driver_role = context.user_data.get('driver_role')
        driver_phone = context.user_data.get('driver_phone')

        # Get group from database
        from ...infrastructure.persistence.database import database
        from ...infrastructure.persistence.group_repository_impl import GroupRepository

        session = database.get_session()
        group_repo = GroupRepository(session)
        group = group_repo.find_by_chat_id(str(context.user_data['setup_group_id']))

        if not group:
            await query.edit_message_text("❌ Error: Group not found.")
            session.close()
            return ConversationHandler.END

        try:
            # Register driver with role from user input
            request = RegisterDriverRequest(
                group_id=group.id,
                name=driver_name,
                phone=driver_phone,
                assigned_vehicle_id=assigned_vehicle_id,
                role=driver_role
            )
            response = self.register_driver_use_case.execute(request)

            # Get vehicle info if assigned
            vehicle_info = ""
            if response.assigned_vehicle_id:
                vehicle = self.vehicle_repository.find_by_id(response.assigned_vehicle_id)
                if vehicle:
                    vehicle_info = f"\nAssigned to: {vehicle.license_plate}"

            await query.edit_message_text(
                f"✅ Driver registered successfully!\n\n"
                f"Name: {response.name}\n"
                f"Phone: {response.phone}\n"
                f"Role: {response.role}"
                f"{vehicle_info}\n\n"
                "The driver can now record trips and fuel."
            )

        except ValueError as e:
            await query.edit_message_text(f"❌ Error: {str(e)}")
        finally:
            session.close()

        return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the conversation"""
        await update.message.reply_text("Setup cancelled.")
        return ConversationHandler.END
