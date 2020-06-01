from flask import Flask, request
from fff_automation.modules import settings
from fff_automation.bots import telebot
import telegram
import os

# SETUP TELEGRAM BOT
global teleTOKEN
global URL
global telegram_bot

teleTOKEN = settings.get_var('BOT_TOKEN')
URL = settings.get_var('SERVER_APP_DOMAIN')
telegram_bot = telegram.Bot(token=teleTOKEN)

app = Flask(__name__)

s = telegram_bot.setWebhook('{URL}{HOOK}'.format(URL=URL, HOOK=teleTOKEN))
if s:
    print("APP: Webhook setup correctly")
else:
    print("APP: Error in setting up webhook")


@app.route('/{}'.format(teleTOKEN), methods=['POST'])
def receive_update():
    print("APP: Received Update")
    update = telegram.Update.de_json(
        request.get_json(force=True), telegram_bot)
    telebot.update_queue.put(update)
    return 'ok'


# RECEIVE OTHER WEBHOOKS
""" @app.route('/other_webhook_route', methods=['POST'])
def receive_child_update(token):
    json_update = request.get_json(force=True)
    do_something(json_update)
    return 'ok' """


@app.route('/')
def index():
    return '.'


if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0',
            port=int(os.environ.get('PORT', 5000)))
