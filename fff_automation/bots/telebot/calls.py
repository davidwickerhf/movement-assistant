from fff_automation.bots.telebot import *

def get_calls(update, context):
    print('TELEBOT: calls()')
    user_id = update.effective_user.id
    user = database.get(user_id, table=database.USERS)[0]

    if user in [None, []]:
        print('TELEBOT: calls(): user is not in web of trust')
        update.message.reply_text(text=no_access_group_info_text, parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    else:
        chat_id = update.effective_chat.id
        botupdate = BotUpdate(update=update, user=update.effective_user)
        if database.get(chat_id)[0] in [None, []]:
            botupdate.message = update.message.reply_text(text=chat_not_registerred_info, parse_mode=ParseMode.HTML)
            return ConversationHandler.END
        else:
            markup = create_menu(['Group Calls', 'All Calls'], [GROUP_CALLS, ALL_CALLS])
            botupdate.message = update.message.reply_text(text=select_calls_group_text, reply_markup=markup, parse_mode=ParseMode.HTML)
            utils.dump_pkl('calls', botupdate)
            return CALLS_SELECTION
        

def calls_selection(update, context):
    print('TELEBOT: calls_group()')
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    botupdate = utils.load_pkl('calls', chat_id, user_id)
    print(botupdate)
    if botupdate == None:
        print('nope')
        return CALLS_SELECTION
    query = update.callback_query
    # GET CALLS
    if int(query.data) == GROUP_CALLS:
        calls = database.get(chat_id, table=database.CALLS, field='chat_id')
        botupdate.obj_selection = GROUP_CALLS
    else:
        calls = database.get(table=database.CALLS)
        botupdate.obj_selection = ALL_CALLS
    # OUT CALL CHOICE
    if len(calls) < 1:
        text = no_calls_text
        botupdate.message.edit_text(text=text, parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    else:
        markup = rotate_calls(botupdate, RIGHT)
        text = select_call_text
        botupdate.message.edit_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML)
        utils.dump_pkl('calls', botupdate)
        return SELECT_CALL


def select_call(update, context):
    print('TELEBOT: group_calls()')
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    botupdate = utils.load_pkl('calls', chat_id, user_id)
    if botupdate == None:
        return SELECT_CALL
    query = update.callback_query
    if query.data in (LEFT, RIGHT):
        markup = rotate_calls(botupdate, query.data)
        text = select_call_text
        botupdate.message.edit_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML)
        utils.dump_pkl('calls', botupdate)
        return GROUP_CALLS
    elif query.data == 'cancel_calls':
        cancel_calls(update, context)
        return ConversationHandler.END
    else:
        botupdate.selected = query.data
        print(botupdate.selected)
        botupdate.obj = database.get(botupdate.selected, table=database.CALLS, field='id')[0]
        text = utils.format_call_info(None, botupdate.obj)
        markup = InlineKeyboardMarkup([[InlineKeyboardButton(text='Trello Card', url=botupdate.get_card_url()), InlineKeyboardButton(text='Edit Info', callback_data=EDIT_CALL)]])
        botupdate.message.edit_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML)
        utils.delete_pkl('calls', chat_id, user_id)
        return ConversationHandler.END


def cancel_calls(update, context):
    print('TELEBOT: cancel_calls()')
    chat_id = update.effective_chat.id
    user_id = update.callback_query.from_user.id
    botupdate = utils.load_pkl('calls', chat_id, user_id)
    update.callback_query.answer()
    if botupdate == None:
        return
    else:
        print("CANCEL PRESSED")
        text = format_group_info(botupdate, type=2, error_text=cancel_edit_group_text)
        markup = format_group_buttons(botupdate.obj)
        botupdate.message.edit_text(
            text=text, parse_mode=ParseMode.HTML, reply_markup=markup)
        utils.delete_pkl('edit_group', chat_id, user_id)
    return ConversationHandler.END


