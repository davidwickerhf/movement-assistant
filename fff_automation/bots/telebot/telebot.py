from fff_automation.bots.telebot import *
from fff_automation.bots.telebot.activate import *
from fff_automation.bots.telebot.editgroup import *
from fff_automation.bots.telebot.deletegroup import *
from fff_automation.bots.telebot.newcall import *
from fff_automation.bots.telebot.feedback import *
from fff_automation.bots.telebot.help import *

def setup(token):
    bot = Bot(token)
    update_queue = Queue()
    job_queue = JobQueue()
    dp = Dispatcher(bot=bot, update_queue=update_queue,
                    use_context=True, job_queue=job_queue)
    job_queue.set_dispatcher(dp)

    # Commands
    dp.add_handler(CommandHandler("help", help))
    group_handler = ConversationHandler(
        entry_points=[CommandHandler("activate", save_group)],
        states={
            GROUP_INFO: [],
            CATEGORY: [CallbackQueryHandler(category)],
            REGION: [CallbackQueryHandler(region)],
            RESTRICTION: [CallbackQueryHandler(restriction)],
            IS_SUBGROUP: [CallbackQueryHandler(is_subgroup)],
            PARENT_GROUP: [CallbackQueryHandler(parent_group)],
            PURPOSE: [MessageHandler(Filters.text, purpose), CallbackQueryHandler(purpose)],
            ONBOARDING: [MessageHandler(Filters.text, onboarding), CallbackQueryHandler(onboarding)],
            TIMEOUT: [MessageHandler(Filters.all, callback=conv_timeout)],
        },
        fallbacks=[],
        conversation_timeout=timedelta(seconds=240),
    )
    edit_group_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(
            edit_group, pattern='^' + 'edit_group' + '$'), CommandHandler('editgroup', edit_group)],
        states={
            ARGUMENT: [CallbackQueryHandler(edit_group_argument)],
            EDIT_IS_SUBGROUP: [CallbackQueryHandler(edit_is_subgroup)],
            EDIT_PARENT: [CallbackQueryHandler(edit_parent)],
            INPUT_ARGUMENT: [CallbackQueryHandler(input_edit_group_argument), MessageHandler(Filters.text, input_edit_group_argument)],
        },
        fallbacks=[CallbackQueryHandler(
            cancel_feedback, pattern='cancel_feedback')]
    )
    delete_group_handler = ConversationHandler(
        entry_points=[CommandHandler('deletegroup', delete_group)],
        states={
            CONFIRM_DELETE_GROUP: [CallbackQueryHandler(confirm_delete_group)],
            DOUBLE_CONFIRM_DELETE_GROUP: [
                CallbackQueryHandler(double_confirm_delete_group)],
            TIMEOUT: [MessageHandler(Filters.all, callback=conv_timeout)]
        },
        fallbacks=[],
        conversation_timeout=timedelta(seconds=240),
    )
    call_handler = ConversationHandler(
        entry_points=[CommandHandler(
            'newcall', new_call), CommandHandler('editcall', edit_call)],
        states={
            CALL_DETAILS: [CallbackQueryHandler(edit_call, pattern='^' + str(EDIT_CALL) + '$')],
            EDIT_CALL: [],
            EDIT_ARGUMENT: [],
            ADD_TITLE: [MessageHandler(Filters.text, add_title), CallbackQueryHandler(cancel_call)],
            ADD_DATE: [MessageHandler(Filters.text, add_date), CallbackQueryHandler(cancel_call)],
            ADD_TIME: [MessageHandler(Filters.text, add_time), CallbackQueryHandler(cancel_call)],
            TIMEOUT: [MessageHandler(Filters.all, callback=conv_timeout)],
        },
        fallbacks=[CallbackQueryHandler(cancel_call)],
        conversation_timeout=timedelta(seconds=240),
    )
    feedback_handler = ConversationHandler(
        entry_points=[CommandHandler('feedback', feedback)],
        states={
            FEEDBACK_TYPE: [CallbackQueryHandler(feedback_type)],
            ISSUE_TYPE: [CallbackQueryHandler(issue_type)],
            INPUT_FEEDBACK: [MessageHandler(Filters.text, input_feedback)]
        },
        fallbacks=[CallbackQueryHandler(
            cancel_feedback, pattern='cancel_feedback')],
    )

    dp.add_handler(group_handler)
    dp.add_handler(edit_group_handler)
    dp.add_handler(delete_group_handler)
    dp.add_handler(call_handler)
    dp.add_handler(feedback_handler)
    dp.add_error_handler(error)

    thread = Thread(target=dp.start, name='dispatcher')
    thread.start()

    return update_queue