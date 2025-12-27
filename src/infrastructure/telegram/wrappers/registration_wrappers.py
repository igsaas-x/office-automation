"""
Group Registration Handler Wrappers
Contains handlers for group registration
"""
from telegram import Update
from telegram.ext import ContextTypes
from ....application.use_cases.register_group import RegisterGroupUseCase
from ....presentation.handlers.registration_handler import RegistrationHandler


def create_registration_wrappers(get_repositories_func):
    """
    Create group registration handler wrappers

    Args:
        get_repositories_func: Function that returns repository dict

    Returns:
        Dict of wrapper functions
    """

    async def register_group_start_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the group registration conversation"""
        repos = get_repositories_func()
        session = repos['session']
        group_repo = repos['group_repo']
        telegram_user_repo = repos['telegram_user_repo']

        try:
            register_group_use_case = RegisterGroupUseCase(group_repo, telegram_user_repo)
            registration_handler = RegistrationHandler(
                register_group_use_case,
                group_repo,
                telegram_user_repo
            )

            return await registration_handler.register_command(update, context)

        finally:
            session.close()

    async def register_group_receive_name_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive business name and complete registration"""
        repos = get_repositories_func()
        session = repos['session']
        group_repo = repos['group_repo']
        telegram_user_repo = repos['telegram_user_repo']

        try:
            register_group_use_case = RegisterGroupUseCase(group_repo, telegram_user_repo)
            registration_handler = RegistrationHandler(
                register_group_use_case,
                group_repo,
                telegram_user_repo
            )

            return await registration_handler.receive_business_name(update, context)

        finally:
            session.close()

    return {
        'register_group_start_wrapper': register_group_start_wrapper,
        'register_group_receive_name_wrapper': register_group_receive_name_wrapper,
    }
