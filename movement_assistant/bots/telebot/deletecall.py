from movement_assistant.bots.telebot import *

def delete_call(update, context):
    botupdate = interface.authenticate(update, context, 0, True)
    
