from fff_automation.bots.telebot import *

def help(update, context):
    update.message.chat.send_message(text=help_description.format(
        new_call_description, new_group_description), parse_mode=ParseMode.HTML)