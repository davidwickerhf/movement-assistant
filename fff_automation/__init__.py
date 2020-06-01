from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from fff_automation.modules import settings
from fff_automation.bots import telebot
import telegram

# SETUP TELEGRAM BOT
global teleTOKEN
global URL
global telegram_bot

teleTOKEN = settings.get_var('BOT_TOKEN')
URL = settings.get_var('SERVER_APP_DOMAIN')
telegram_bot = telegram.Bot(token=teleTOKEN)
update_queue = telebot.setup(settings.get_var('BOT_TOKEN'))

app = Flask(__name__)
app.config['SECRET_KEY'] = ''
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

from fff_automation import routes
