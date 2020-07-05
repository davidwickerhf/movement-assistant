from fff_automation.bots.telebot import *

def group_info(update, context):
    print('TELEBOT: group_info()')
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    user = database.get(user_id, table=database.USERS)[0]
    if user == None:
        print('TELEBOT: group_info(): User is not registered in web of trust')
        update.message.reply_text(text=no_access_group_info_text, parse_mode=ParseMode.HTML)
    else:
        print('TELEBOT: group_indo(): User has access to web of trust')
        group = database.get(chat_id)[0]
        botupdate = BotUpdate(obj=group, update=update, user=update.effective_user)
        if group == None:
            update.message.reply_text(text=chat_not_registerred_info, parse_mode=ParseMode.HTML)
        else:
            text = format_group_info(botupdate, type=3)
            keyboard = [[InlineKeyboardButton("Trello Card", url=str('https://trello.com/c/{}'.format(group.card_id))), InlineKeyboardButton("Edit Info", callback_data='edit_group')]]
            markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML)
