"""
Setup Handler Wrappers
Contains handlers for vehicle and driver setup
"""
from telegram import Update
from telegram.ext import ContextTypes
from ....application.use_cases.register_vehicle import RegisterVehicleUseCase
from ....application.use_cases.register_group import RegisterGroupUseCase
from ....application.use_cases.delete_vehicle import DeleteVehicleUseCase
from ....presentation.handlers.setup_handler import SetupHandler


def create_setup_wrappers(get_repositories_func):
    """
    Create setup handler wrappers

    Args:
        get_repositories_func: Function that returns repository tuple

    Returns:
        Dict of wrapper functions
    """

    def build_setup_handler(include_group: bool = False):
        """Build a setup handler instance with necessary dependencies"""
        session, _, _, _, group_repo, _, vehicle_repo, trip_repo, fuel_repo, _ = get_repositories_func()
        setup_handler = SetupHandler(
            RegisterVehicleUseCase(vehicle_repo),
            None,  # RegisterDriverUseCase - driver functionality removed
            RegisterGroupUseCase(group_repo) if include_group else None,
            vehicle_repo,
            None,  # driver_repo - driver functionality removed
            DeleteVehicleUseCase(vehicle_repo, trip_repo, fuel_repo),
            None  # DeleteDriverUseCase - driver functionality removed
        )
        return session, setup_handler

    async def setup_menu_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, setup_handler = build_setup_handler(include_group=True)
        result = await setup_handler.setup_menu(update, context)
        session.close()
        return result

    async def setup_vehicle_start_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, setup_handler = build_setup_handler()
        result = await setup_handler.start_vehicle_setup(update, context)
        session.close()
        return result

    async def setup_vehicle_plate_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, setup_handler = build_setup_handler()
        result = await setup_handler.receive_vehicle_plate(update, context)
        session.close()
        return result

    async def setup_vehicle_driver_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, setup_handler = build_setup_handler()
        result = await setup_handler.receive_vehicle_driver_name(update, context)
        session.close()
        return result

    async def setup_driver_start_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, setup_handler = build_setup_handler()
        result = await setup_handler.start_driver_setup(update, context)
        session.close()
        return result

    async def setup_driver_name_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, setup_handler = build_setup_handler()
        result = await setup_handler.receive_driver_name(update, context)
        session.close()
        return result

    async def setup_driver_role_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, setup_handler = build_setup_handler()
        result = await setup_handler.receive_driver_role(update, context)
        session.close()
        return result

    async def setup_driver_phone_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, setup_handler = build_setup_handler()
        result = await setup_handler.receive_driver_phone(update, context)
        session.close()
        return result

    async def setup_driver_vehicle_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, setup_handler = build_setup_handler()
        result = await setup_handler.receive_driver_vehicle(update, context)
        session.close()
        return result

    async def setup_list_vehicles_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, setup_handler = build_setup_handler()
        result = await setup_handler.list_vehicles(update, context)
        session.close()
        return result

    async def setup_list_drivers_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, setup_handler = build_setup_handler()
        result = await setup_handler.list_drivers(update, context)
        session.close()
        return result

    async def setup_delete_vehicle_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, setup_handler = build_setup_handler()
        result = await setup_handler.delete_vehicle(update, context)
        session.close()
        return result

    async def setup_delete_driver_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, setup_handler = build_setup_handler()
        result = await setup_handler.delete_driver(update, context)
        session.close()
        return result

    async def setup_back_to_menu_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        session, setup_handler = build_setup_handler(include_group=True)
        result = await setup_handler.back_to_setup_menu(update, context)
        session.close()
        return result

    async def cancel_setup_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle cancel button from setup menu"""
        from telegram.ext import ConversationHandler
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("❌ ការរៀបចំត្រូវបានបោះបង់។")
        return ConversationHandler.END

    return {
        'setup_menu_wrapper': setup_menu_wrapper,
        'setup_vehicle_start_wrapper': setup_vehicle_start_wrapper,
        'setup_vehicle_plate_wrapper': setup_vehicle_plate_wrapper,
        'setup_vehicle_driver_wrapper': setup_vehicle_driver_wrapper,
        'setup_driver_start_wrapper': setup_driver_start_wrapper,
        'setup_driver_name_wrapper': setup_driver_name_wrapper,
        'setup_driver_role_wrapper': setup_driver_role_wrapper,
        'setup_driver_phone_wrapper': setup_driver_phone_wrapper,
        'setup_driver_vehicle_wrapper': setup_driver_vehicle_wrapper,
        'setup_list_vehicles_wrapper': setup_list_vehicles_wrapper,
        'setup_list_drivers_wrapper': setup_list_drivers_wrapper,
        'setup_delete_vehicle_wrapper': setup_delete_vehicle_wrapper,
        'setup_delete_driver_wrapper': setup_delete_driver_wrapper,
        'setup_back_to_menu_wrapper': setup_back_to_menu_wrapper,
        'cancel_setup_wrapper': cancel_setup_wrapper,
    }
