from fff_automation.bots.telebot import *


######################### FEEDBACK CONVERSATION FUNCTIONS ###############
@run_async
def feedback(update, context):
    print("TELEBOT: feedback()")
    # Create Feedback Type Menu & Message Text
    markup = create_menu([
        interface.githubc.label_keys.get(interface.githubc.ISSUE),
        interface.githubc.label_keys.get(interface.githubc.FEATURE_REQUEST),
        interface.githubc.label_keys.get(interface.githubc.FEEDBACK),
        interface.githubc.label_keys.get(interface.githubc.QUESTION),
        'Cancel'
    ], [
        interface.githubc.ISSUE,
        interface.githubc.FEATURE_REQUEST,
        interface.githubc.FEEDBACK,
        interface.githubc.QUESTION,
        'cancel_feedback'
    ])

    # Create Feedback Obj
    feedback = Feedback(
        user_id=update.effective_user.id,
        chat_id=update.effective_chat.id,
        date=utils.now_time()
    )

    # Send Message
    feedback.message = update.message.chat.send_message(
        text=select_feedback_type, parse_mode=ParseMode.HTML, reply_markup=markup)

    # Save feedback obj in pickle
    utils.dump_pkl('feedback', feedback)
    return FEEDBACK_TYPE


@run_async
def feedback_type(update, context):
    print('TELEBOT: feedback_type()')
    # Retrieve Feedback Obj from pickle
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    feedback = utils.load_pkl('feedback', chat_id, user_id)

    if feedback == '' or user_id != feedback.user_id:
        print('TELEBOT: feedback_type: Wrong User')
        return FEEDBACK_TYPE

    # Check if callback-query is 'cancel_feedback'
    if update.callback_query.data == 'cancel_feedback':
        cancel_feedback(update, context)
        return ConversationHandler.END

    # Save selected type in obj
    feedback.type = int(update.callback_query.data)
    print('TELEBOT: feedback_type(): Got Feedback Type: ', feedback.type)
    if feedback.type == interface.githubc.ISSUE:
        # TYPE IS ISSUE
        # Send issue type menu
        markup = create_menu(button_titles=[
            interface.githubc.issue_types.get(interface.githubc.ACTIVATE),
            interface.githubc.issue_types.get(interface.githubc.ALL_GROUPS),
            interface.githubc.issue_types.get(interface.githubc.ARCHIVE_GROUP),
            interface.githubc.issue_types.get(
                interface.githubc.UNARCHIVE_GROUP),
            interface.githubc.issue_types.get(interface.githubc.DELETE_GROUP),
            interface.githubc.issue_types.get(interface.githubc.NEW_CALL),
            interface.githubc.issue_types.get(interface.githubc.ALL_CALLS),
            interface.githubc.issue_types.get(interface.githubc.DELETE_CALL),
            interface.githubc.issue_types.get(interface.githubc.TRUST_USER),
            interface.githubc.issue_types.get(interface.githubc.OTHER),
            'Cancel'
        ], callbacks=[
            interface.githubc.ACTIVATE,
            interface.githubc.ALL_GROUPS,
            interface.githubc.ARCHIVE_GROUP,
            interface.githubc.UNARCHIVE_GROUP,
            interface.githubc.DELETE_GROUP,
            interface.githubc.NEW_CALL,
            interface.githubc.ALL_CALLS,
            interface.githubc.DELETE_CALL,
            interface.githubc.TRUST_USER,
            interface.githubc.OTHER,
            'cancel_feedback'
        ], cols=2)
        print('TELEBOT: issue_type(): Created Markup')
        update.callback_query.edit_message_text(
            select_issue_type, parse_mode=ParseMode.HTML)
        update.callback_query.edit_message_reply_markup(markup)
        feedback.message = update.callback_query.message
        # Save feedback obj in pickle
        utils.dump_pkl('feedback', feedback)
        return ISSUE_TYPE
    else:
        # TYPE IS EITHER QUESTION, FEEDBACK OR FEATURE REQUEST
        # Send message asking for input
        print('TELEBOT: Feedback is NOT an issue')
        markup = create_menu('Canel', 'cancel_feedback')
        update.callback_query.edit_message_text(send_feedback_input.format(
            interface.githubc.label_keys.get(feedback.type)), parse_mode=ParseMode.HTML)
        feedback.message = update.callback_query.message
        # Save feedback obj in pickle
        utils.dump_pkl('feedback', feedback)
        return INPUT_FEEDBACK


@run_async
def issue_type(update, context):
    print('TELEBOT: issue_feedback()')
    # Retrieve feedback obj from pickle
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    feedback = utils.load_pkl('feedback', chat_id, user_id)
    print('TELEBOT: issue_type')

    if feedback == '' or user_id != feedback.user_id:
        return ISSUE_TYPE

    # Check if callback-query is 'cancel_feedback'
    if update.callback_query.data == 'cancel_feedback':
        cancel_feedback(update, context)
        return ConversationHandler.END

    # Save selected status (issue type) in obj
    feedback.issue_type = int(update.callback_query.data)

    # Send message requesting issue description
    markup = create_menu('Canel', 'cancel_feedback')
    update.callback_query.edit_message_text(send_issue_input.format(
        interface.githubc.label_keys.get(feedback.type)), parse_mode=ParseMode.HTML)
    update.callback_query.edit_message_reply_markup(markup)
    feedback.message = update.callback_query.message
    # Save feedback obj in pickle
    utils.dump_pkl('feedback', feedback)
    return INPUT_FEEDBACK


@run_async
@send_typing_action
def input_feedback(update, context):
    print('TELEBOT: issue_type()')
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    feedback = utils.load_pkl('feedback', chat_id, user_id)

    if feedback == '' or user_id != feedback.user_id:
        return INPUT_FEEDBACK

    # Processing Message
    feedback.message.delete()
    feedback.message = update.message.reply_text('Processing...')

    # Save issue
    message_text = save_feedback(feedback, update)

    # Send message to developer
    devs = settings.get_var('DEVS')
    for dev_id in devs:
        context.bot.send_message(dev_id, message_text,
                                 parse_mode=ParseMode.HTML)

    # Send confirm message in chat
    feedback.message.delete()
    text = '{} thank you for your feedback! Your input has been sent to my developers'.format(
        update.effective_user.name)
    update.effective_chat.send_message(text, parse_mode=ParseMode.HTML)

    # Delete Persistence File
    utils.delete_pkl('feedback', chat_id, user_id)
    return ConversationHandler.END


def save_feedback(feedback, update):
    # Format feedback body
    type_int = feedback.get_type()
    issue_type_int = feedback.get_issue_type()
    body = '''**{} by {}:**
    **Issue Type:** {}
    **Recorded on:** {}
    **User id:** {}
    **Chat id:** {}
    **Chat Name:** {}
    **Issue Body:** {}'''.format(
        interface.githubc.label_keys.get(type_int),
        update.effective_user.name,
        interface.githubc.issue_types.get(issue_type_int),
        feedback.date,
        feedback.user_id,
        feedback.chat_id,
        update.effective_chat.title,
        update.message.text)
    feedback.body = body
    feedback.title = '{} by {}'.format(
        interface.githubc.label_keys.get(feedback.type), update.effective_user.name,)

    # Save feedback in database / GitHub
    feedback = interface.feedback(feedback)

    # Send message to developers
    message = '<b>{} by {}</b>:\n\n<b>Issue Type:</b> {}\n<b>Recorded on:</b> {}\n<b>User id:</b> {}\n<b>Chat id:</b> {}\n<b>Chat Name:</b> {}\n<b>Issue Body:</b> {}\n<b>Issue Url</b>: {}\n<b>Issue Json:</b> {}'.format(
        interface.githubc.label_keys.get(feedback.type),
        mention_html(update.effective_user.id,
                     update.effective_user.first_name),
        interface.githubc.issue_types.get(feedback.issue_type),
        feedback.date,
        feedback.user_id,
        feedback.chat_id,
        update.effective_chat.title,
        update.message.text,
        feedback.url,
        feedback.json)
    return message


@run_async
@send_typing_action
def cancel_feedback(update, context):
    # GET CALL SAVED IN PERSISTANCE FILE
    chat_id = update.effective_chat.id
    user_id = update.callback_query.from_user.id
    feedback = utils.load_pkl('feedback', chat_id, user_id)
    update.callback_query.answer()
    if feedback == "" or user_id != feedback.user_id:
        return
    else:
        print("CANCEL PRESSED")
        feedback.message.edit_text(
            text=cancel_feedback_text, parse_mode=ParseMode.HTML)
        utils.delete_pkl('feedback', chat_id, user_id)
    return ConversationHandler.END
