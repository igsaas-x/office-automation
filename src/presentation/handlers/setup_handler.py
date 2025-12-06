from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from typing import Optional
from ...application.use_cases.register_vehicle import RegisterVehicleUseCase
from ...application.use_cases.register_driver import RegisterDriverUseCase
from ...application.use_cases.register_group import RegisterGroupUseCase
from ...application.use_cases.delete_vehicle import DeleteVehicleUseCase
from ...application.use_cases.delete_driver import DeleteDriverUseCase
from ...application.dto.vehicle_dto import RegisterVehicleRequest
from ...application.dto.driver_dto import RegisterDriverRequest
from ...domain.repositories.vehicle_repository import IVehicleRepository
from ...domain.repositories.driver_repository import IDriverRepository

# Conversation states
SETUP_MENU = 0
# Vehicle registration states
SETUP_VEHICLE_PLATE = 10
SETUP_VEHICLE_DRIVER = 11
# Driver registration states
SETUP_DRIVER_NAME = 20
SETUP_DRIVER_ROLE = 21
SETUP_DRIVER_PHONE = 22
SETUP_DRIVER_VEHICLE = 23

class SetupHandler:
    def __init__(
        self,
        register_vehicle_use_case: RegisterVehicleUseCase,
        register_driver_use_case: Optional[RegisterDriverUseCase] = None,
        register_group_use_case: Optional[RegisterGroupUseCase] = None,
        vehicle_repository: IVehicleRepository = None,
        driver_repository: Optional[IDriverRepository] = None,
        delete_vehicle_use_case: Optional[DeleteVehicleUseCase] = None,
        delete_driver_use_case: Optional[DeleteDriverUseCase] = None
    ):
        self.register_vehicle_use_case = register_vehicle_use_case
        self.register_driver_use_case = register_driver_use_case
        self.register_group_use_case = register_group_use_case
        self.vehicle_repository = vehicle_repository
        self.driver_repository = driver_repository
        self.delete_vehicle_use_case = delete_vehicle_use_case
        self.delete_driver_use_case = delete_driver_use_case

    def _get_group(self, context: ContextTypes.DEFAULT_TYPE):
        """Retrieve group by chat_id stored in user_data."""
        from ...infrastructure.persistence.database import database
        from ...infrastructure.persistence.group_repository_impl import GroupRepository

        session = database.get_session()
        group_repo = GroupRepository(session)
        group_id = context.user_data.get('setup_group_id')
        group = None
        if group_id:
            group = group_repo.find_by_chat_id(str(group_id))
        return group, session

    async def setup_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show setup menu with vehicle and driver options"""
        chat = update.effective_chat

        # Register group if not already registered
        if self.register_group_use_case:
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
            [InlineKeyboardButton("🚗 បញ្ចូលឡាន", callback_data="setup_vehicle")],
            [InlineKeyboardButton("📋 បញ្ជីឡាន", callback_data="list_vehicles")],
        ]

        # Only show driver options if driver functionality is enabled
        if self.register_driver_use_case:
            keyboard.extend([
                [InlineKeyboardButton("👤 បញ្ចូលអ្នកបើកបរ", callback_data="setup_driver")],
                [InlineKeyboardButton("📋 បញ្ជីអ្នកបើកបរ", callback_data="list_drivers")],
            ])

        keyboard.append([InlineKeyboardButton("❌ បោះបង់", callback_data="cancel_setup")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        message_text = "⚙️ ម៉ឺនុយបញ្ចូល\n\n"
        if self.register_driver_use_case:
            message_text += (
                "សូមជ្រើសរើសអ្វីដែលត្រូវបញ្ចូល:\n\n"
                "បញ្ចូលឡានជាមុនសិន បន្ទាប់មកអ្នកបើកបរ។\n"
                "អ្នកក៏អាចមើលបញ្ជី ឬលុបធាតុដែលមានស្រាប់បាន។"
            )
        else:
            message_text += (
                "សូមជ្រើសរើសអ្វីដែលត្រូវបញ្ចូល:\n\n"
                "អ្នកអាចបញ្ចូលឡាន និងគ្រប់គ្រងក្រុមឡានរបស់អ្នក។"
            )

        if update.callback_query:
            await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message_text, reply_markup=reply_markup)

        return SETUP_MENU

    # ==================== Management ====================

    async def list_vehicles(self, update: Update, context: ContextTypes.DEFAULT_TYPE, skip_answer: bool = False):
        """List vehicles with delete options"""
        query = update.callback_query
        if not skip_answer:
            await query.answer()

        # Ensure group ID is stored
        if 'setup_group_id' not in context.user_data:
            context.user_data['setup_group_id'] = update.effective_chat.id

        group, session = self._get_group(context)
        if not group:
            await query.edit_message_text("❌ កំហុស: រកមិនឃើញក្រុម។ សូមព្យាយាម /setup ម្តងទៀត។")
            session.close()
            return ConversationHandler.END

        vehicles = self.vehicle_repository.find_by_group_id(group.id)
        session.close()

        type_emoji = {"TRUCK": "🚚", "VAN": "🚐", "MOTORCYCLE": "🏍️", "CAR": "🚗"}
        lines = ["🚗 ឡាន", ""]
        keyboard = []

        if not vehicles:
            lines.append("រកមិនឃើញឡានទេ។\n\nប្រើបញ្ចូលឡានដើម្បីបន្ថែមមួយ។")
        else:
            for idx, vehicle in enumerate(vehicles, 1):
                emoji = type_emoji.get(vehicle.vehicle_type, "🚗")
                lines.append(f"{idx}. {emoji} {vehicle.license_plate}")
                keyboard.append([
                    InlineKeyboardButton(
                        f"🗑️ លុប {vehicle.license_plate}",
                        callback_data=f"delete_vehicle_{vehicle.id}"
                    )
                ])

        keyboard.append([InlineKeyboardButton("⬅️ ត្រឡប់ទៅបញ្ចូល", callback_data="back_to_setup")])

        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return SETUP_MENU

    async def list_drivers(self, update: Update, context: ContextTypes.DEFAULT_TYPE, skip_answer: bool = False):
        """List drivers with delete options"""
        # Driver functionality disabled
        if not self.driver_repository:
            query = update.callback_query
            await query.answer("មុខងារអ្នកបើកបរមិនអាចប្រើបានទេ")
            return SETUP_MENU

        query = update.callback_query
        if not skip_answer:
            await query.answer()

        if 'setup_group_id' not in context.user_data:
            context.user_data['setup_group_id'] = update.effective_chat.id

        group, session = self._get_group(context)
        if not group:
            await query.edit_message_text("❌ កំហុស: រកមិនឃើញក្រុម។ សូមព្យាយាម /setup ម្តងទៀត។")
            session.close()
            return ConversationHandler.END

        drivers = self.driver_repository.find_by_group_id(group.id)
        vehicles = self.vehicle_repository.find_by_group_id(group.id)
        vehicle_map = {v.id: v for v in vehicles}
        session.close()

        lines = ["👤 អ្នកបើកបរ", ""]
        keyboard = []

        if not drivers:
            lines.append("រកមិនឃើញអ្នកបើកបរទេ។\n\nប្រើបញ្ចូលអ្នកបើកបរដើម្បីបន្ថែមមួយ។")
        else:
            for idx, driver in enumerate(drivers, 1):
                vehicle_label = ""
                if driver.assigned_vehicle_id and driver.assigned_vehicle_id in vehicle_map:
                    vehicle_label = f" - {vehicle_map[driver.assigned_vehicle_id].license_plate}"
                lines.append(f"{idx}. 👤 {driver.name} ({driver.phone}){vehicle_label}")
                keyboard.append([
                    InlineKeyboardButton(
                        f"🗑️ លុប {driver.name}",
                        callback_data=f"delete_driver_{driver.id}"
                    )
                ])

        keyboard.append([InlineKeyboardButton("⬅️ ត្រឡប់ទៅបញ្ចូល", callback_data="back_to_setup")])

        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return SETUP_MENU

    async def delete_vehicle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete selected vehicle"""
        query = update.callback_query
        vehicle_id = int(query.data.replace("delete_vehicle_", ""))

        if 'setup_group_id' not in context.user_data:
            context.user_data['setup_group_id'] = update.effective_chat.id

        group, session = self._get_group(context)
        if not group:
            await query.answer("រកមិនឃើញក្រុម", show_alert=True)
            session.close()
            return ConversationHandler.END

        try:
            response = self.delete_vehicle_use_case.execute(group.id, vehicle_id)
            await query.answer(f"បានលុប {response.license_plate}")
        except ValueError as e:
            await query.answer(str(e), show_alert=True)
            session.close()
            return SETUP_MENU

        session.close()
        return await self.list_vehicles(update, context, skip_answer=True)

    async def delete_driver(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete selected driver"""
        # Driver functionality disabled
        if not self.delete_driver_use_case:
            query = update.callback_query
            await query.answer("មុខងារអ្នកបើកបរមិនអាចប្រើបានទេ")
            return SETUP_MENU

        query = update.callback_query
        driver_id = int(query.data.replace("delete_driver_", ""))

        if 'setup_group_id' not in context.user_data:
            context.user_data['setup_group_id'] = update.effective_chat.id

        group, session = self._get_group(context)
        if not group:
            await query.answer("រកមិនឃើញក្រុម", show_alert=True)
            session.close()
            return ConversationHandler.END

        try:
            response = self.delete_driver_use_case.execute(group.id, driver_id)
            await query.answer(f"បានលុប {response.name}")
        except ValueError as e:
            await query.answer(str(e), show_alert=True)
            session.close()
            return SETUP_MENU

        session.close()
        return await self.list_drivers(update, context, skip_answer=True)

    async def back_to_setup_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Return to setup menu"""
        if update.callback_query:
            await update.callback_query.answer()
        return await self.setup_menu(update, context)

    # ==================== Vehicle Registration ====================

    async def start_vehicle_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start vehicle registration flow"""
        query = update.callback_query
        await query.answer()

        await query.edit_message_text(
            "សូមបញ្ចូលស្លាកលេខឡាន:\n"
            "ឧទាហរណ៍: PP-1234 ឬ 2A-5678"
        )

        return SETUP_VEHICLE_PLATE

    async def receive_vehicle_plate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive vehicle license plate and ask for driver name"""
        license_plate = update.message.text.strip()

        # Store license plate in context
        context.user_data['vehicle_license_plate'] = license_plate

        # Ask for driver name with skip option
        keyboard = [[InlineKeyboardButton("⏭️ រំលង (គ្មានអ្នកបើកបរ)", callback_data="vehicle_skip_driver")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"ស្លាកលេខឡាន: {license_plate}\n\n"
            "សូមបញ្ចូលឈ្មោះអ្នកបើកបរសម្រាប់ឡាននេះ:\n\n"
            "ឬចុចរំលង ប្រសិនបើឡាននេះមិនមានអ្នកបើកបរកំណត់។",
            reply_markup=reply_markup
        )

        return SETUP_VEHICLE_DRIVER

    async def receive_vehicle_driver_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive vehicle driver name and save vehicle"""
        # Get driver name from message or callback
        driver_name = None
        if update.callback_query:
            await update.callback_query.answer()
            # User clicked skip button
            driver_name = None
        else:
            # User provided driver name
            driver_name = update.message.text.strip()

        license_plate = context.user_data.get('vehicle_license_plate')

        # Get group from database to get its ID
        from ...infrastructure.persistence.database import database
        from ...infrastructure.persistence.group_repository_impl import GroupRepository

        session = database.get_session()
        group_repo = GroupRepository(session)
        group = group_repo.find_by_chat_id(str(context.user_data['setup_group_id']))

        if not group:
            error_msg = "❌ កំហុស: រកមិនឃើញក្រុម។ សូមព្យាយាមម្តងទៀត។"
            if update.callback_query:
                await update.callback_query.edit_message_text(error_msg)
            else:
                await update.message.reply_text(error_msg)
            session.close()
            return ConversationHandler.END

        try:
            # Register vehicle with optional driver name
            request = RegisterVehicleRequest(
                group_id=group.id,
                license_plate=license_plate,
                vehicle_type="TRUCK",  # Default type
                driver_name=driver_name
            )
            response = self.register_vehicle_use_case.execute(request)

            # Show success message
            success_msg = (
                f"✅ ឡានត្រូវបានចុះឈ្មោះដោយជោគជ័យ!\n\n"
                f"ស្លាកលេខឡាន: {response.license_plate}\n"
            )
            if driver_name:
                success_msg += f"អ្នកបើកបរ: {driver_name}\n"

            if update.callback_query:
                await update.callback_query.edit_message_text(success_msg)
            else:
                await update.message.reply_text(success_msg)

        except ValueError as e:
            error_msg = f"❌ កំហុស: {str(e)}"
            if update.callback_query:
                await update.callback_query.edit_message_text(error_msg)
            else:
                await update.message.reply_text(error_msg)
        finally:
            session.close()

        return ConversationHandler.END

    # ==================== Driver Registration ====================

    async def start_driver_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start driver registration flow"""
        # Driver functionality disabled
        if not self.register_driver_use_case:
            query = update.callback_query
            await query.answer("មុខងារអ្នកបើកបរមិនអាចប្រើបានទេ")
            return SETUP_MENU

        query = update.callback_query
        await query.answer()

        await query.edit_message_text(
            "👤 បញ្ចូលអ្នកបើកបរ\n\n"
            "សូមបញ្ចូលឈ្មោះអ្នកបើកបរ:"
        )

        return SETUP_DRIVER_NAME

    async def receive_driver_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive driver name"""
        # Driver functionality disabled
        if not self.register_driver_use_case:
            await update.message.reply_text("មុខងារអ្នកបើកបរមិនអាចប្រើបានទេ")
            return ConversationHandler.END

        driver_name = update.message.text.strip()
        context.user_data['driver_name'] = driver_name

        await update.message.reply_text(
            f"ឈ្មោះ: {driver_name}\n\n"
            "សូមបញ្ចូលតួនាទីអ្នកបើកបរ:\n"
            "ឧទាហរណ៍: អ្នកបើកបរ, អ្នកគ្រប់គ្រង, អ្នកត្រួតពិនិត្យ"
        )

        return SETUP_DRIVER_ROLE

    async def receive_driver_role(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive driver role"""
        # Driver functionality disabled
        if not self.register_driver_use_case:
            await update.message.reply_text("មុខងារអ្នកបើកបរមិនអាចប្រើបានទេ")
            return ConversationHandler.END

        driver_role = update.message.text.strip()
        context.user_data['driver_role'] = driver_role

        await update.message.reply_text(
            f"ឈ្មោះ: {context.user_data['driver_name']}\n"
            f"តួនាទី: {driver_role}\n\n"
            "សូមបញ្ចូលលេខទូរសព្ទអ្នកបើកបរ:\n"
            "ឧទាហរណ៍: 012345678"
        )

        return SETUP_DRIVER_PHONE

    async def receive_driver_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive driver phone and show vehicle selection"""
        # Driver functionality disabled
        if not self.register_driver_use_case:
            await update.message.reply_text("មុខងារអ្នកបើកបរមិនអាចប្រើបានទេ")
            return ConversationHandler.END

        driver_phone = update.message.text.strip()
        context.user_data['driver_phone'] = driver_phone

        # Get group from database
        from ...infrastructure.persistence.database import database
        from ...infrastructure.persistence.group_repository_impl import GroupRepository

        session = database.get_session()
        group_repo = GroupRepository(session)
        group = group_repo.find_by_chat_id(str(context.user_data['setup_group_id']))

        if not group:
            await update.message.reply_text("❌ កំហុស: រកមិនឃើញក្រុម។")
            session.close()
            return ConversationHandler.END

        # Get all vehicles for this group
        vehicles = self.vehicle_repository.find_by_group_id(group.id)
        session.close()

        if not vehicles:
            await update.message.reply_text(
                "⚠️ រកមិនឃើញឡានទេ!\n\n"
                "សូមបញ្ចូលឡានជាមុនសិនដោយប្រើ /setup → បញ្ចូលឡាន"
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
        keyboard.append([InlineKeyboardButton("⏭️ រំលង - កំណត់ពេលក្រោយ", callback_data="assign_vehicle_skip")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"ឈ្មោះ: {context.user_data['driver_name']}\n"
            f"ទូរសព្ទ: {driver_phone}\n\n"
            "កំណត់ទៅឡាន:",
            reply_markup=reply_markup
        )

        return SETUP_DRIVER_VEHICLE

    async def receive_driver_vehicle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive vehicle assignment and save driver"""
        # Driver functionality disabled
        if not self.register_driver_use_case:
            query = update.callback_query
            await query.answer("មុខងារអ្នកបើកបរមិនអាចប្រើបានទេ")
            return ConversationHandler.END

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
            await query.edit_message_text("❌ កំហុស: រកមិនឃើញក្រុម។")
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
                    vehicle_info = f"\nកំណត់ទៅ: {vehicle.license_plate}"

            await query.edit_message_text(
                f"✅ អ្នកបើកបរត្រូវបានចុះឈ្មោះដោយជោគជ័យ!\n\n"
                f"ឈ្មោះ: {response.name}\n"
                f"ទូរសព្ទ: {response.phone}\n"
                f"តួនាទី: {response.role}"
                f"{vehicle_info}\n\n"
                "អ្នកបើកបរឥឡូវអាចកត់ត្រាដំណើរ និងសាំងបាន។"
            )

        except ValueError as e:
            await query.edit_message_text(f"❌ កំហុស: {str(e)}")
        finally:
            session.close()

        return ConversationHandler.END

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the conversation"""
        await update.message.reply_text("ការបញ្ចូលត្រូវបានបោះបង់។")
        return ConversationHandler.END
