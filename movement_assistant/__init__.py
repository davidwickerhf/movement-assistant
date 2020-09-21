from flask import Flask
from sqlalchemy import SQLAlchemy
from movement_assistant.modules import settings
from movement_assistant.bots.telebot import telebot
import telegram

# SETUP TELEGRAM BOT
global teleTOKEN
global URL
global telegram_bot

# TELEGRAM VARIABLES
teleTOKEN = settings.get_var('BOT_TOKEN')
URL = settings.get_var('SERVER_APP_DOMAIN')
telegram_bot = telegram.Bot(token=teleTOKEN)
update_queue = telebot.setup(settings.get_var('BOT_TOKEN'))

# Setup Flask
app = Flask(__name__)
