from fff_automation.bots.telebot import *

def calls(update, context):
    print('TELEBOT: calls()')
    user_id = update.effective_user.id
    user = database.get(user_id, table=database.USERS)[0]

    if user in [None, []]:
        print('TELEBOT: calls(): user is not in web of trust')
        update.message.reply_text(text=no_access_group_info_text, parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    else:
        chat_id = update.effective_chat.id
        if database.get(chat_id)[0] not in [None, []]:
            update.message.reply_text(text=not_registered_text, parse_mode=ParseMode.HTML)
        markup = create_menu(['Group Calls', 'All Calls'], [])
        update.message.reply_text(text=select_calls_group_text, reply_markup=markup, parse_mode=ParseMode.HTML)
        
        return CALLS_GROUP
        
        """ calls = database.get(chat_id, table=database.CALLS, field='chat_id')
        if len(calls) < 1:
            text = no_calls_text
            update.message.reply_text(text=text, parse_mode=ParseMode.HTML)
            return ConversationHandler.END
        else:
            markup = rotate_calls()
            text = select_call_text
            update.message.reply_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML)
            return  """

def calls_group(update, context):
    print('TELEBOT: calls_group()')




def group_calls(update, context):
    print('TELEBOT: group_calls()')

def all_calls(update, context):
    print('TELEBOT: all_calls()')

def edit_call(update, context):
    print('TELEBOT: edit_call()')


