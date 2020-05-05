from flask import Flask, request
from modules import settings
from bots import telebot
import telegram

global teleTOKEN
global URL
global telegram_bot

teleTOKEN = settings.get_var('BOT_TOKEN')
URL = settings.get_var('SERVER_APP_DOMAIN')
telegram_bot = telegram.Bot(token=teleTOKEN)
server = Flask(__name__)

if settings.LOCAL == True:
    print("APP: Running locally, launching telegram bot without running Flask Server.")
    telebot.main(None)
else:
    print("APP: Running on server, launching Flask server.")


@server.route('/{}'.format(teleTOKEN), methods=['POST'])
def receive_update():
    update = telegram.Update.de_json(
        request.get_json(force=True), telegram_bot)
    telebot.main(update)
    return 'ok'


@server.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    # we use the bot object to link the bot to our app which live
    # in the link provided by URL
    s = telegram_bot.setWebhook('{URL}{HOOK}'.format(URL=URL, HOOK=teleTOKEN))
    # something to let us know things work
    if s:
        print("APP: Webhook setup correctly")
        return "webhook setup ok"
    else:
        print("APP: Error in setting up webhook")
        return "webhook setup failed"


# RECEIVE OTHER WEBHOOKS
""" @server.route('/other_webhook_route', methods=['POST'])
def receive_child_update(token):
    json_update = request.get_json(force=True)
    do_something(json_update)
    return 'ok' """


@server.route('/')
def index():
    return '.'


if __name__ == '__main__':
    server.run(threaded=True)
